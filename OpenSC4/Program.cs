using System;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.Security.Cryptography;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Net.Http.Headers;
using System.Dynamic;
using System.Reflection;

namespace OpenSC4
{
    class Program
    {
        public enum SubfileTypes
        {
            Directory,      // e86b1eef     e86b1eef    286b1f03
            TerrainMap,     // a9dd6ff4     e98f9525    00000001
            NetworkIndex,   // 6a0f82b2     -           -
            Network1,       // c9c05c6e     -           -
            Network2,       // ca16374f     -           -
            Exemplars,      // 6534284a     -           -
            Unidentified    // all other
        }
        public struct SubfileIdentifiers
        {
            public SubfileTypes type;
            public uint typeID;
            public uint groupID;
            public uint instanceID;
            public uint IDdepth;
        }
        public static SubfileIdentifiers[] KnownSubfiles = new SubfileIdentifiers[] {
            new SubfileIdentifiers(){
                type = SubfileTypes.Directory,
                typeID = 3899334383,            // e86b1eef
                groupID = 3899334383,           // e86b1eef
                instanceID = 678108931,         // 286b1f03
                IDdepth = 3
            },
            new SubfileIdentifiers(){
                type = SubfileTypes.TerrainMap,
                typeID = 2849861620,            // a9dd6ff4
                groupID = 3918501157,           // e98f9525
                instanceID = 1,                 // 00000001
                IDdepth = 3
            },
            new SubfileIdentifiers(){
                type = SubfileTypes.NetworkIndex,
                typeID = 1779401394,            // 6a0f82b2
             // groupID = 0,
             // instanceID = 0,
                IDdepth = 1
            },
            new SubfileIdentifiers(){
                type = SubfileTypes.Network1,
                typeID = 3384826990,            // c9c05c6e
             // groupID = 0,
             // instanceID = 0,
                IDdepth = 1
            },
            new SubfileIdentifiers(){
                type = SubfileTypes.Network2,
                typeID = 3390453583,            // ca16374f
             // groupID = 0,
             // instanceID = 0,
                IDdepth = 1
            },
            new SubfileIdentifiers(){
                type = SubfileTypes.Exemplars,
                typeID = 1697917002,            // 6534284a
             // groupID = 0,
             // instanceID = 0,
                IDdepth = 1
            }
        };
        
        public struct FileRef
        {
            public bool exists;     // exists - has been set
            public uint position;     // position - offset into file
            public uint size;     // size - size of referenced file
        }
        public struct Subfile
        {
            public bool exists;
            public uint position;
            public uint size;
            public bool compressed;
            public uint decompressedSize;
            public byte[] data;
            public SubfileTypes type;
        }
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

            // get index ref
            FileRef index = GetFileIndex(open);
            
            Console.WriteLine("> Index Location: " + UintHexLog(index.position));
            Console.WriteLine("> Index Size: " + UintHexLog(index.size));

            Console.WriteLine("");

            // 1.5 Check for DIR file (compression on files)
            FileRef dir = GetDirSubfile(open, index);

            if(dir.exists)
            {
                Console.WriteLine("Parts of file are compressed...");
                Console.WriteLine("> Directory file offset: " + UintHexLog(dir.position));
                Console.WriteLine("> Directory file size: " + UintHexLog(dir.size));
                Console.WriteLine("");
            }
            else
            {
                Console.WriteLine("No compression on the file.");
                Console.WriteLine("");
            }

            /* uint[] dirMetafile = CheckForDBPFCompression(indexOffset, indexSize, open);
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
            }*/

            // Decompression!!!  https://wiki.sc4devotion.com/index.php?title=DBPF_Compression


            // 2. Find index listing for Terrain Data
            //
            Subfile terrainSubfile = LoadSubfile(open, index, dir, SubfileTypes.TerrainMap);

            if (terrainSubfile.exists)
            {
                Console.WriteLine("Terrain Data Found!");
                Console.WriteLine("");
                Console.WriteLine("> Terrain file offset: " + UintHexLog(terrainSubfile.position));
                Console.WriteLine("> Terrain file size: " + UintHexLog(terrainSubfile.size));
                
                if (terrainSubfile.compressed)
                {
                    // Decompress terrain file before reading
                    Console.WriteLine("> Terrain file decompressed size: " + UintHexLog(terrainSubfile.decompressedSize));
                    Console.WriteLine("");
                    Console.WriteLine("Terrain Data has been decompressed...");
                }
                Console.WriteLine("Loaded Terrain Data successfully!");
                Console.WriteLine("");
                Console.WriteLine("Extracting floating point data (terrain height)...");
                
                // ignore first two bytes

                // cast to single (32 bit float)
                Single[] points = new Single[(terrainSubfile.data.Length - (terrainSubfile.data.Length % 4)) / 4];

                for (int i = 0; i < points.Length; i++)
                {
                    points[i] = ToSingleBigEndian(terrainSubfile.data, (i * 4) + 2);
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

            Console.WriteLine("");
            Console.WriteLine("= = = = =");
            Console.WriteLine("");

            // 
            // Network Subfile (Roads)
            // 

            Console.WriteLine("TODO: Load Network Subfile 1 for Road Placement");

            // Get Network Index

            Console.WriteLine("");

            // 
            // Exemplars (> Terrain Exemplars > Sea Level)
            // 

            Console.WriteLine("TODO: Load Exemplar files...");


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
        public static SubfileTypes ResolveIdentifiers (uint typeID)
        {
            foreach (SubfileIdentifiers s in KnownSubfiles)
            {
                if (s.typeID == typeID)
                {
                    if(s.IDdepth == 1)
                    {
                        return s.type;
                    }
                    else
                    {
                        Console.WriteLine("More than one type found, requires groupID and/or instanceID.");
                    }
                }
            }

            return SubfileTypes.Unidentified;
        }
        public static SubfileTypes ResolveIdentifiers(uint typeID, uint groupID)
        {
            foreach(SubfileIdentifiers s in KnownSubfiles)
            {
                if (s.typeID == typeID)
                {
                    if (s.IDdepth >= 2)
                    {
                        if(s.groupID == groupID)
                        {
                            if (s.IDdepth >= 3)
                            {
                                Console.WriteLine("More than one type found, requires instanceID.");
                            }
                            else
                            {
                                return s.type;
                            }
                            
                        }
                    }
                    else
                    {
                        return s.type;
                    }
                }
            }

            return SubfileTypes.Unidentified;
        }
        public static SubfileTypes ResolveIdentifiers(uint typeID, uint groupID, uint instanceID)
        {
            foreach (SubfileIdentifiers s in KnownSubfiles)
            {
                if (s.typeID == typeID)
                {
                    if (s.IDdepth >= 2)
                    {
                        if (s.groupID == groupID)
                        {
                            if (s.IDdepth >= 3)
                            {
                                if(s.instanceID == instanceID)
                                {
                                    return s.type;
                                }
                            }
                            else
                            {
                                return s.type;
                            }

                        }
                    }
                    else
                    {
                        return s.type;
                    }
                }
            }

            return SubfileTypes.Unidentified;
        }
        public static FileRef GetFileIndex(FileStream file)
        {
            byte[] buffer32 = new byte[4];          // 32-bit (4 byte) buffer
            FileRef output = new FileRef();              // output FileRef

            // read index 
            file.Seek(40, SeekOrigin.Begin);           // index reference is always 40 bytes into a SC4 file
            
            // get index position
            file.Read(buffer32, 0, 4);
            output.position = ToInt32LittleEndian(buffer32, 0); 

            // get index size
            file.Read(buffer32, 0, 4);
            output.size = ToInt32LittleEndian(buffer32, 0);

            // successfully retrieved
            output.exists = true;

            return output;
        }
        public static Subfile LoadSubfile(FileStream file, FileRef index, FileRef dir, SubfileTypes type)
        {
            byte[] buffer32 = new byte[4];
            Subfile output = new Subfile();

            // get pos/size from index
            FileRef subfileRef = ReadIndex(file, index, type);
            output.position = subfileRef.position;
            output.size = subfileRef.size;

            // check if subfile is in the Dir list
            output.decompressedSize = FindCompressedSubfile(file, dir, type);
            output.compressed = output.decompressedSize == 0 ? false : true;

            byte[] arbBuf;
            file.Seek(output.position, SeekOrigin.Begin);

            if (output.compressed)
            {
                // if yes, decompress data before loading
                arbBuf = new byte[output.decompressedSize];
                file.Read(arbBuf, 0, (int)output.decompressedSize);

                output.data = DecompressDBPF(arbBuf, 0, output.size, output.decompressedSize);
                output.exists = true;
            }
            else
            {
                // if no, load data directly from indexed location
                arbBuf = new byte[output.size];
                file.Read(arbBuf, 0, (int)output.size);

                output.data = arbBuf;
                output.exists = true;
            }
            output.type = type;

            return output;
        }
        public static byte[] DecompressDBPF(byte[] compressed, uint fileOffset, uint compressedSize, uint decompressedSize)
        {
            // https://wiki.sc4devotion.com/index.php?title=DBPF_Compression

            //Console.WriteLine("");
            //Console.WriteLine("Decompressing..");

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
                uint t = ToInt32LittleEndian(buffer32, 0);      // typeID
                file.Read(buffer32, 0, 4);
                uint g = ToInt32LittleEndian(buffer32, 0);      // groupID
                file.Read(buffer32, 0, 4);
                uint i = ToInt32LittleEndian(buffer32, 0);      // instanceID
                file.Read(buffer32, 0, 4);
                uint fl = ToInt32LittleEndian(buffer32, 0);     // file location (offset where file starts)
                file.Read(buffer32, 0, 4);
                uint fs = ToInt32LittleEndian(buffer32, 0);     // file size

                if (ResolveIdentifiers(t, g, i) == SubfileTypes.TerrainMap)
                {
                    outOffset = fl;
                    outSize = fs;
                    break;
                }
                if (file.Position >= off + siz)
                    break;
            }

            return new uint[] { outOffset, outSize };
        }
        public static FileRef GetDirSubfile(FileStream file, FileRef index)
        {
            return ReadIndex(file, index, SubfileTypes.Directory);
        }
        public static FileRef ReadIndex(FileStream file, FileRef index, SubfileTypes type)   // look for a specific subfile in index
        {
            byte[] buffer32 = new byte[4];  // 32-bit (4 byte) buffer
            FileRef output = new FileRef();      // output FileRef
            bool seeking = true;

            file.Seek(index.position, SeekOrigin.Begin);

            while (seeking)
            {
                file.Read(buffer32, 0, 4);
                uint tID = ToInt32LittleEndian(buffer32, 0);      // typeID
                file.Read(buffer32, 0, 4);
                uint gID = ToInt32LittleEndian(buffer32, 0);      // groupID
                file.Read(buffer32, 0, 4);
                uint iID = ToInt32LittleEndian(buffer32, 0);      // instanceID
                file.Read(buffer32, 0, 4);
                uint fl = ToInt32LittleEndian(buffer32, 0);     // file location (offset where file starts)
                file.Read(buffer32, 0, 4);
                uint fs = ToInt32LittleEndian(buffer32, 0);     // file size

                if (ResolveIdentifiers(tID, gID, iID) == type)
                {
                    output.position = fl;
                    output.size = fs;
                    output.exists = true;
                    break;
                }
                if (file.Position >= index.position + index.size)
                    break;
            }
            return output;
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
                uint t = ToInt32LittleEndian(buffer32, 0);      // typeID
                file.Read(buffer32, 0, 4);
                uint g = ToInt32LittleEndian(buffer32, 0);      // groupID
                file.Read(buffer32, 0, 4);
                uint i = ToInt32LittleEndian(buffer32, 0);      // instanceID
                file.Read(buffer32, 0, 4);
                uint fl = ToInt32LittleEndian(buffer32, 0);     // file location (offset where file starts)
                file.Read(buffer32, 0, 4);
                uint fs = ToInt32LittleEndian(buffer32, 0);     // file size

                if (ResolveIdentifiers(t, g, i) == SubfileTypes.Directory)
                {
                    outOffset = fl;
                    outSize = fs;
                    break;
                }
                if (file.Position >= indexOffset + indexSize)
                    break;
            }

            return new uint[] { outOffset, outSize };
        }
        public static uint FindCompressedSubfile(FileStream file, FileRef dir, SubfileTypes type)
        {
            byte[] buffer32 = new byte[4];
            bool seeking = true;
            file.Seek(dir.position, SeekOrigin.Begin);

            uint outSize = 0;

            while (seeking)
            {
                file.Read(buffer32, 0, 4);
                uint t = ToInt32LittleEndian(buffer32, 0);  // typeID
                file.Read(buffer32, 0, 4);
                uint g = ToInt32LittleEndian(buffer32, 0);  // groupID
                file.Read(buffer32, 0, 4);
                uint i = ToInt32LittleEndian(buffer32, 0); // instanceID
                file.Read(buffer32, 0, 4);
                uint uncompressedSize = ToInt32LittleEndian(buffer32, 0);

                if (ResolveIdentifiers(t, g, i) == type)
                {
                    outSize = uncompressedSize;
                    
                }
                if (file.Position >= dir.position + dir.size)
                    break;
            }

            return outSize;
        }
    }
}
