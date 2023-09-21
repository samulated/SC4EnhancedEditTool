using System;
using System.Text;
using System.Threading.Tasks;
using System.IO;

namespace OpenSC4
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Start of SC4 LOAD Script ===");
            Console.WriteLine("");

            string path = "D:\\Projects\\SC4 TerraRoad\\City - A Terra.sc4";

            Console.WriteLine("Loading file: " + path);

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

            Console.WriteLine("Index Location: " + indexOffset);

            // get index size
            open.Seek(44, SeekOrigin.Begin);
            open.Read(buffer32, 0, 4);
            uint indexSize = ToInt32LittleEndian(buffer32, 0);

            Console.WriteLine("Index Size: " + indexSize);

            Console.WriteLine("");

            // 1.5 Check for DIR file (compression on files)

            uint[] dirMetafile = CheckForDBPFCompression(indexOffset, indexSize, open);
            uint terrainDataCompressedSize = 0;

            if (dirMetafile[0] != 0)
            {
                Console.WriteLine("Parts of file are compressed...");
                Console.WriteLine("Checking for TerrainData");
                Console.WriteLine("");

                uint dirOffset = dirMetafile[0];
                uint dirSize = dirMetafile[1];

                // Check for compressed TerrainData - > https://wiki.sc4devotion.com/index.php?title=DBDF
                terrainDataCompressedSize = FindCompressedTerrainData(dirOffset, dirSize, open);
                if (terrainDataCompressedSize != 0)
                {
                    Console.WriteLine("Compressed TerrainData found...");
                    Console.WriteLine("");
                }
            }
            else
            {
                Console.WriteLine("No compression on file, proceeding to terrain data.");
                Console.WriteLine("");
            }

            // TODO: Decompression!!!

            /*
            // 2. Find index listing for Terrain Data
            //
            int[] terrainMetafile = FindTerrainData(indexOffset, indexSize, open);

            if (terrainMetafile[0] != 0)
            {
                Console.WriteLine("Terrain Data Found!");

                // 3. Get the terrain data chunk
                int terrainFileOffset = terrainMetafile[0];
                int terrainFileSize = terrainMetafile[1];

                Console.WriteLine("");
                Console.WriteLine("Terrain file offset: " + terrainFileOffset);
                Console.WriteLine("Terrain file size: " + terrainFileSize);
                Console.WriteLine("");

                byte[] terrainData = new byte[terrainFileSize];

                open.Seek(terrainFileOffset, SeekOrigin.Begin);
                open.Read(terrainData, 0, terrainFileSize);

                Console.WriteLine("Loaded Terrain Data successfully!");
                Console.WriteLine("");

            }
            else
            {
                Console.WriteLine("No terrain data..");
            }
            */



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
