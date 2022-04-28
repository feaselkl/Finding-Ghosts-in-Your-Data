# Finding Ghosts in Your Data:  The Code Base
This code base includes a **completed** form of everything created over the course of _Finding Ghosts in Your Data_.  If you wish to follow along with the book and create your own solution in line with mine, please read the next section.  If you prefer instead simply to review my code and run it directly, read the following section.

## Play Along at Home
If you wish to create your own solution, I recommend renaming the `app` folder in the `code\src` directory to something like `app_complete`.  That way, you still have a completed version of the application to refer back against.  Then, when following along with the book, you can create your own `app` folder.

If you follow this practice and want to use a Docker-based solution, you should not need to modify the `Dockerfile` at all.  If you are running things locally, kick off the API process with the following command:

`uvicorn app.main:app --host 0.0.0.0 --port 80`

And should you wish instead to see how the completed version of the app works, make a minor change to the call:

`uvicorn app_complete.main:app --host 0.0.0.0 --port 80`

Should you wish to deploy the completed version as a Docker container, you can edit the `Dockerfile` to copy `./src/app_complete` instead of `./src/app`, though leave the destination directory alone.

If you are proficient with Docker, you may also wish to build one image based on the completed code and tag it separately:

`docker build -t anomalydetector_complete .`

Then, when building your own version of the detector, tag it as mentioned in the book:

`docker build -t anomalydetector .`

This will allow you to compare how your service behaves compared to the version in the book.

## Try the Completed Product
If you simply want to run the completed product, execute the following command inside the `code` directory:

`uvicorn app.main:app --host 0.0.0.0 --port 80`