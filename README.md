# SC4 Enhanced Edit Tool (SEET)
This is some old code I was using to see if I could open up SC4 files (SimCity 4 save files) and extract the geometry info from them so I could potentially visualise how they would look when translated into The Sims 2 (which uses SC4 files as the base terrain and road info for their neighborhoods)

At the time it was called OpenSC4, but in the interest of not being confused with an open-source SC4 implementation (which would be super cool, by the way) I have renamed to the SC4 Enhanced Edit Tool.

Down the track I'd like to add terrain edit functionality so that one might fine tune the neighborhood geometry more exactly, and maybe even road editing (with helpers/checkers for lot placement in game) which will probably be much harder to implement.
Ideally I would like these edited files to be loadable still by both games, but there's some checksum shenanigans that happen that may make that a little difficult.

Regardless I wanted to get back into it, since TS2 Legacy Edition has been released, to give people a nicer way of creating neighborhoods, as I've personally always found jumping between the games (and the axis flip that happens) hard to wrap my head around.

## Current Implementation
Right now this is mostly just some scripts that load data and put into an object for use by something else.

I have plugged it into a Unity scene to test it out, mapping the terrain co-ords onto a terrain grid in-engine. It looked alright, honestly. Screenshots of this below.

![SC4 Screenshot](https://github.com/samulated/SC4EnhancedEditTool/blob/main/sc4_tool_example1.jpg)
![In-engine Screenshot](https://github.com/samulated/SC4EnhancedEditTool/blob/main/sc4_tool_example2.jpg)
![TS2 Screenshot](https://github.com/samulated/SC4EnhancedEditTool/blob/main/sc4_tool_example3.jpg)

As you can see, the data extraction part is working (once you do some scaling fixes and such)
Will probably not do an actual implementation in Unity, but it's cool that it Just Works when you grab the data out.
