beach lots

at least 3 squares (1 sc4 square gap) away from water

water floor should be around 16 squares below



4 Lot
4 SC4 units of height = 32 sims 2 units of heights

therefore 1 SC4z = 6 S2z

0.5 SC4z should be appx 3 S2z

We will need to perform increment testing to see if the neighhborhood 'snaps' or interpets heights smoothly

sc4 use doubles that seem only have 0.X degree of accuracy above the hood.


3 x 3 lots

L - H - D from sidewalk

1 - 1 - 15
2 - 1 - 25
3 - 2 - 15 | 24
4 - 3 - 12 | 17 | 25
5 - 3 - 15 | 22 | 27
6 - 4 - 12 | 17 | 22 | 27
7 - 5 - 11 | 14 | 18 | 22 | 27
8 - 5 - 12 | 17 | 21 | 24 | 28
9 - 6 - 11 | 14 | 18 | 21 | 24 | 28
10- 7 - 11 | 13 | 16 | 18 | 21 | 24 | 28
11- 7 - 11 | 14 | 18 | 21 | 23 | 26 | 28
12- 8 - 11 | 13 | 16 | 18 | 21 | 23 | 26 | 28
13- 9 - 11 | 12 | 15 | 16 | 19 | 21 | 23 | 26 | 28
14- 9 - 11 | 13 | 16 | 18 | 21 | 22 | 25 | 26 | 29
15- 10- 11 | 12 | 15 | 16 | 19 | 20 | 23 | 24 | 27 | 28
16- 11- 10 | 12 | 14 | 15 | 17 | 19 | 21 | 22 | 25 | 26 | 29

3 x 4 lots placed on other side of road from 3 x 3s (might have affected 10 square lot smoothing that seems to apply automatically)
1 - 1 - 5
2 - 1 - 15
3 - 2 - 5 | 14
...
testing further up line
...
6 - 4 - 2 | 7 | 12 | 17

in line with expectations, the sides of the lot seem to be diagonal for 20 squares, and then flat for the remaining 20
this appears to be due to flattening not being applied to the first 10 squares
may check in clone of neighborhood without 3x3s already placed whether the 10 square flat zone applies for freshly placed lots 

should be able to verify larger heights' differences now though.

14   - 1 | 3 | 6 | 8 | 11 | 12 | 15 | 16 | 19

it turns out the 10 square flat zone is purely based on lot direction

but i think we can consistantly declare that 0.15 SC4y = 1 TS2y


1.8 = 12 aka walk in basement height




