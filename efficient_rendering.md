Notes for efficeint rendering:

update game screen at least 60 times per second.

means we need a max of  of 17 ms per update.
this also means the max latency we can afford is 17 ms per update.


if the game give us a data a rate of 60 messages per second on the server, and we have a worst case latency of 
100 ms,then we are only going to get 10 messaegs per second actually.what if we send in batches of 6 frames per 
message and at each render we draw 6 frames?

2 ms is worst case runtime for rendering an update so we can afford to do this. this will let our game run smoothly even
with high latency.

Questions:
    - will it be possibvle for the game to get much farther ahead in ticks than the rednering (will cause inputs form the user to be delayed)
