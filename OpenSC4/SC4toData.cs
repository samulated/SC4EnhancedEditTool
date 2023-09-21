using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;

namespace OpenSC4
{
    class SC4toData
    {
        static string path = "D:\\Projects\\SC4 TerraRoad\\City - A Terra.sc4";

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

        // 1. Get the Index
        // Index is stored at location stated at a u32 starting at byte 40 of header 
        // Index size is stored next to it in a u32 starting at byte 44 of header

    }
}
