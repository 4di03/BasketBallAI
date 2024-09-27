<h1> AI HOOPS </h1>

Play a live demo at:

https://ai-hoops1.herokuapp.com

See the code at:

https://github.com/4di03/AI-Hoops


Controls for singleplayer are A to jump left and D to jump right.


The AI is trained using the NEAT neuroevolution algorithm, and you can read more about it here:  
https://nn.cs.utexas.edu/downloads/papers/stanley.cec02.pdf


You can using the training section configure the neuroevolution process and craft the best AI that will be saved locally.
If your AI beats the record of the globally best AI, it will replace it as the 'record best AI'!

TODO:
 - increase concurrency by bumping number of workers using nginx or swapping to uWSGI. See [docs](https://flask-socketio.readthedocs.io/en/latest/deployment.html#gunicorn-web-server)
 - remove coupling of framerate to ball velocity/gravity
 - Death animation in Solo mode
 - NEAT NN DISPLAY during training
 - No Graphics Training
 - Model saved indication
   
## Dev Instructions ## 

Run the game using Docker:

```bash
docker compose build # only for when you change dependencies or Dockerfile

docker compose up

```

Run the game using venv:

```bash
pip install virtualenv # (first time only)

virtualenv -p <python path> venv # (first time only)

source venv/bin/activate


pip install -r requirements.txt # (first time only)

bash run.bash
```
