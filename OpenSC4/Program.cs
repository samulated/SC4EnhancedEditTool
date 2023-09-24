using System;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.Security.Cryptography;
using System.Linq;

namespace OpenSC4
{
    class Program
    {
        static void Main(string[] args)
        {   Console.WriteLine("=== Start of SC4 LOAD Script ===");
            Console.WriteLine("");

            string path = Environment.CurrentDirectory + "\\Test Files\\City - Mesa Canyon.sc4";

            Console.WriteLine("Loading file: " + path);
            Console.WriteLine("");

            // https://wiki.sc4devotion.com/index.php?title=DBPF SC4 file breakdown
            // DBPF file with an index offset and size listed in the header
            // 1. Get the index
            // 2. Find index listing for Terrain Data
            // 3. Get the terrain data chunk
            // 4. Cast terrain data onto usable data types
            // 5. Display / Edit data
            // 6. Save terrain data back into the file, and save out
            // 7. Test
            //

            // =====
            // 0. Load file

            FileStream open = File.Open(path, FileMode.Open);

            Console.WriteLine("File Loaded...");

            // 1. Get the Index
            // Index is stored at location stated at a u32 starting at byte 40 of header 
            // Index size is stored next to it in a u32 starting at byte 44 of header

            byte[] buffer32 = new byte[4];

            // get index location
            open.Seek(40, SeekOrigin.Begin);
            open.Read(buffer32, 0, 4);
            uint indexOffset = ToInt32LittleEndian(buffer32, 0);

            Console.WriteLine("> Index Location: " + UintHexLog(indexOffset));

            // get index size
            open.Seek(44, SeekOrigin.Begin);
            open.Read(buffer32, 0, 4);
            uint indexSize = ToInt32LittleEndian(buffer32, 0);

            Console.WriteLine("> Index Size: " + UintHexLog(indexSize));

            Console.WriteLine("");

            // 1.5 Check for DIR file (compression on files)

            uint[] dirMetafile = CheckForDBPFCompression(indexOffset, indexSize, open);
            uint terrainDataDecompressedSize = 0;

            if (dirMetafile[0] != 0)
            {
                uint dirOffset = dirMetafile[0];
                uint dirSize = dirMetafile[1];

                Console.WriteLine("Parts of file are compressed...");
                Console.WriteLine("> Directory file offset: " + UintHexLog(dirOffset));
                Console.WriteLine("> Directory file size: " + UintHexLog(dirSize));
                Console.WriteLine("");
                Console.WriteLine("Checking for TerrainData in compression directory...");
                Console.WriteLine("");

                

                // Check for compressed TerrainData - > https://wiki.sc4devotion.com/index.php?title=DBDF
                terrainDataDecompressedSize = FindCompressedTerrainData(dirOffset, dirSize, open);
                if (terrainDataDecompressedSize != 0)
                {
                    Console.WriteLine("Compressed TerrainData found...");
                    Console.WriteLine("> Decompressed file size: " + UintHexLog(terrainDataDecompressedSize));
                    Console.WriteLine("");
                }
                else
                {
                    Console.WriteLine("No Compressed TerrainData found.");
                    Console.WriteLine("");
                }
            }
            else
            {
                Console.WriteLine("No compression on file, proceeding to terrain data.");
                Console.WriteLine("");
            }

            // TODO: Decompression!!!  https://wiki.sc4devotion.com/index.php?title=DBPF_Compression

            
            // 2. Find index listing for Terrain Data
            //
            uint[] terrainMetafile = FindTerrainData(indexOffset, indexSize, open);

            if (terrainMetafile[0] != 0)
            {
                Console.WriteLine("Terrain Data Found!");

                // 3. Get the terrain data chunk
                uint terrainFileOffset = terrainMetafile[0];
                uint terrainFileSize = terrainMetafile[1];

                Console.WriteLine("");
                Console.WriteLine("> Terrain file offset: " + UintHexLog(terrainFileOffset));
                Console.WriteLine("> Terrain file size: " + UintHexLog(terrainFileSize));

                byte[] terrainData;
                byte[] terrainFileBuffer = new byte[terrainFileSize];

                open.Seek(terrainFileOffset, SeekOrigin.Begin);
                open.Read(terrainFileBuffer, 0, (int)terrainFileSize);

                // Check if Compressed
                if (terrainDataDecompressedSize != 0)
                {
                    // Decompress terrain file before reading
                    Console.WriteLine("> Terrain file decompressed size: " + UintHexLog(terrainDataDecompressedSize));
                    Console.WriteLine("");

                    terrainData = DecompressDBPF(terrainFileBuffer, terrainFileOffset, terrainFileSize, terrainDataDecompressedSize);
                    Console.WriteLine("terrainData Has been decompressed...");
                }
                else
                {
                    // Read terrain file without decompressing
                    Console.WriteLine("");

                    terrainData = new byte[terrainFileSize];
                    terrainData = terrainFileBuffer;

                }

                Console.WriteLine("Loaded Terrain Data successfully!");
                Console.WriteLine("");
                Console.WriteLine("Extracting floating point data (terrain height)...");
                // ignore first two bytes

                // cast to single (32 bit float)
                Single[] points = new Single[(terrainData.Length - (terrainData.Length % 4)) / 4];

                for (int i = 0; i < points.Length; i++)
                {
                    points[i] = ToSingleBigEndian(terrainData, (i * 4) + 2);
                }

                Console.WriteLine("Floating points extracted!");
                Console.WriteLine("Casting to grid..");
                // cast onto X by Y grid ? (2d array maybe?)
                if (Math.Sqrt(points.Length) % 1 == 0)
                {
                    int gridSize = (int)Math.Sqrt(points.Length);

                    Single[,] grid = new Single[gridSize, gridSize];

                    for (int i = 0; i < gridSize; i++)
                    {
                        for (int j = 0; j < gridSize; j++)
                        {
                            int k = i + j * gridSize;
                            grid[i, j] = points[k];
                        }
                    }
                    Console.WriteLine("Data has been casted to a " + gridSize + " square grid.");
                }
                else
                {
                    Console.WriteLine("Terrain Data is not square");
                }
            }
            else
            {
                Console.WriteLine("No terrain data..");
            }
            



            //
            // End of script 
            //

            Console.WriteLine("");
            Console.WriteLine("=== End of SC4 LOAD Script ===");
            Console.WriteLine("");

            
        }

        public static uint ToInt32BigEndian(byte[] buf, int i)
        {
            return (uint)((buf[i] << 24) | (buf[i + 1] << 16) | (buf[i + 2] << 8) | buf[i + 3]);
        }
        public static uint ToInt32LittleEndian(byte[] buf, int i)
        {
            return (uint)((buf[i+3] << 24) | (buf[i + 2] << 16) | (buf[i + 1] << 8) | buf[i]);
        }
        public static Single ToSingleBigEndian(byte[] buf, int i)
        {
            return BitConverter.ToSingle(buf, i);
        }
        public static Single ToSingleLittleEndian(byte[] buf, int i)
        {
            byte[] arbBuf = new byte[4];
            arbBuf[3] = buf[i];
            arbBuf[2] = buf[i + 1];
            arbBuf[1] = buf[i + 2];
            arbBuf[0] = buf[i + 3];

            return BitConverter.ToSingle(arbBuf, i);
        }
        public static string UintHexLog(uint i)
        {
            string hex = i.ToString("X");
            return i + " | " + hex;
        }
        public static byte[] DecompressDBPF(byte[] compressed, uint fileOffset, uint compressedSize, uint decompressedSize)
        {
            // https://wiki.sc4devotion.com/index.php?title=DBPF_Compression

            Console.WriteLine("");
            Console.WriteLine("Decompressing..");

            int i = 0;      //iterator
            byte[] arbBuf;  //byte buffer of arbitrary size
            byte[] outBuf = new byte[decompressedSize];  //output buffer
            // # 1. Read the first 4 bytes
            // This is the size of the following header + compressed data.
            uint cSizeCheck = ToInt32LittleEndian(compressed, i);
            i += 4;

            // # 2. Read Header
            // 5 byte header comprising of:
            // - Compression ID (0x10FB) (QFS Compression)
            // - Uncompressed Size of File
            arbBuf = new byte[4];
            arbBuf[0] = compressed[i];
            arbBuf[1] = compressed[i + 1];
            arbBuf[2] = 0;
            arbBuf[3] = 0;
            i += 2;

            uint compressionID = ToInt32LittleEndian(arbBuf, 0);

            arbBuf = new byte[4];
            arbBuf[0] = 0;
            arbBuf[1] = compressed[i];
            arbBuf[2] = compressed[i + 1];
            arbBuf[3] = compressed[i + 2];
            i += 3;

            uint dSizeCheck = ToInt32BigEndian(arbBuf, 0);  // flipped endianness because that makes sense

            // # 3. Read compressed data
            // 
            int j = 0;

            while (i < compressedSize)
            {
                uint controlCharacter = 0;
                uint controlCharacterSize = 0;
                uint plainTextAppend = 0;
                uint outputWriteAmount = 0; // Amount of bytes to write 
                uint outputWriteOffset = 0; // Offset is from end of output buffer (eg 0 is last byte, 1 is second to last byte, etc.)
                // offset writing happens one byte at a time, so as we loop through even the newly appended bytes can be re-appended as many times as needed

                // Inspect Control Character
                arbBuf = new byte[4] { 0, 0, 0, compressed[i] };

                uint ccCheck = ToInt32BigEndian(arbBuf, 0);

                //evaluate cc
                if (ccCheck < 128)          // 0x00 - 0x7F
                {
                    controlCharacterSize = 2;
                    plainTextAppend = (uint)(compressed[0] & 3);                                                                // byte0 & 0x03
                    outputWriteAmount = (uint)(((compressed[0] & 28) >> 2) + 2);                                                // ((byte0 & 0x1C) >> 2) + 3
                    outputWriteOffset = (uint)(((compressed[0] & 96) << 3) + compressed[i + 1] + 1);                            // ((byte0 & 0x60) << 3) + byte1 + 1
                }
                else if (ccCheck < 192)     // 0x80 - 0xBF
                {
                    controlCharacterSize = 3;
                    plainTextAppend = (uint)(((compressed[0 + 1] & 192) >> 6) & 3);                                             // ((byte1 & 0xC0) >> 6) & 0x03
                    outputWriteAmount = (uint)((compressed[0] & 63) + 4);                                                       // (byte0 & 0x3F) + 4
                    outputWriteOffset = (uint)(((compressed[1] & 63) << 8) + compressed[i + 2] + 1);                            // ((byte1 & 0x3F) << 8) + byte2 + 1
                }
                else if (ccCheck < 224)     // 0xC0 - 0xDF
                {
                    controlCharacterSize = 4;
                    plainTextAppend = (uint)(compressed[i] & 3);                                                                // byte0 & 0x03
                    outputWriteAmount = (uint)(((compressed[i] & 12) << 6) + compressed[i + 3] + 5);                            // (byte0 & 0x3F) + 4
                    outputWriteOffset = (uint)(((compressed[i] & 16) << 12) + (compressed[i + 1] << 8) + compressed[i+2] + 1);  // ((byte0 & 0x10) << 12) + (byte1 << 8) + byte2 + 1
                }
                else if (ccCheck < 252)     // 0xE0 - 0xFB
                {
                    controlCharacterSize = 1;
                    plainTextAppend = (uint)(((compressed[i] & 31) << 2 ) + 4);                                                 // ((byte0 & 0x1F) << 2 ) + 4
                  //outputWriteAmount                                                                                           // 0
                  //outputWriteOffset                                                                                           // -
                }
                else if (ccCheck < 256)     // 0xFC - 0xFF
                {
                    controlCharacterSize = 1;
                    plainTextAppend = (uint)(compressed[i] & 3);                                                                // (byte0 & 0x03)
                  //outputWriteAmount                                                                                           // 0
                  //outputWriteOffset                                                                                           // -
                }
                else                        // invalid value
                {
                    break;
                }

                i += (int)controlCharacterSize;

                for (int k = 0; k < plainTextAppend; k++)
                {
                    outBuf[j] = compressed[i];
                    j++;
                    i++;
                }

                for (int k = 0; k < outputWriteAmount; k++)
                {
                    outBuf[j] = outBuf[j - outputWriteOffset];
                    j++;
                }
            }

            return outBuf;
        }
        public static uint[] FindTerrainData(uint off, uint siz, FileStream file)
        {
            byte[] buffer32 = new byte[4];
            bool seeking = true;
            file.Seek(off, SeekOrigin.Begin);

            uint outOffset = 0;
            uint outSize = 0;

            while (seeking)
            {
                file.Read(buffer32, 0, 4);
                uint typeID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint groupID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint instanceID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint fileLocation = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint fileSize = ToInt32LittleEndian(buffer32, 0);

                if (typeID == 2849861620)
                {
                    if (groupID == 3918501157)
                    {
                        if (instanceID == 1)
                        {
                            outOffset = fileLocation;
                            outSize = fileSize;
                            break;
                        }
                    }
                }
                if (file.Position >= off + siz)
                    break;
            }

            return new uint[] { outOffset, outSize };
        }
        public static uint[] CheckForDBPFCompression(uint indexOffset, uint indexSize, FileStream file)
        {
            byte[] buffer32 = new byte[4];
            bool seeking = true;

            file.Seek(indexOffset, SeekOrigin.Begin);

            uint outOffset = 0;
            uint outSize = 0;

            while (seeking)
            {
                file.Read(buffer32, 0, 4);
                uint typeID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint groupID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint instanceID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint fileLocation = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint fileSize = ToInt32LittleEndian(buffer32, 0);

                if (typeID == 3899334383)
                {
                    if (groupID == 3899334383)
                    {
                        if (instanceID == 678108931)
                        {
                            outOffset = fileLocation;
                            outSize = fileSize;
                            break;
                        }
                    }
                }
                if (file.Position >= indexOffset + indexSize)
                    break;
            }

            return new uint[] { outOffset, outSize };
        }
        public static uint FindCompressedTerrainData(uint off, uint siz, FileStream file)
        {
            byte[] buffer32 = new byte[4];
            bool seeking = true;
            file.Seek(off, SeekOrigin.Begin);

            uint outSize = 0;

            while (seeking)
            {
                file.Read(buffer32, 0, 4);
                uint typeID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint groupID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint instanceID = ToInt32LittleEndian(buffer32, 0);
                file.Read(buffer32, 0, 4);
                uint uncompressedSize = ToInt32LittleEndian(buffer32, 0);

                if (typeID == 2849861620)
                {
                    if (groupID == 3918501157)
                    {
                        if (instanceID == 1)
                        {
                            outSize = uncompressedSize;
                        }
                    }
                }
                if (file.Position >= off + siz)
                    break;
            }

            return outSize;
        }
    }
}
