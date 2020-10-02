import praw
import os
from imageai.Detection import ObjectDetection
import random
import config

class PizzaPoster:
    def __init__(self, subreddit, debug = False):
        self.subreddit = subreddit
        self.posts = []
        self.debug = debug
        self.reddit = praw.Reddit(
            client_id = config.redditInfo["client_id"],
            client_secret = config.redditInfo["client_secret"],
            password = config.redditInfo["password"],
            username = config.redditInfo["username"],
            user_agent = config.redditInfo["user_agent"]
        )
        self.detector = self.setupDetector()

    # setup model detection
    def setupDetector(self):
        detector = ObjectDetection()
        detector.setModelTypeAsRetinaNet()
        detector.setModelPath(os.path.join(os.getcwd(), f"model/{config.model_path}"))
        detector.loadModel()
        self.log("created detector")
        return detector

    # pull last 5 new posts
    def fetchPosts(self):
        sub = self.reddit.subreddit(self.subreddit)
        for post in sub.new(limit=5):
            # if we have replied don't fetch the post
            if not self.hasReplied(post):
                self.log(f"pushing posts: {post.url}")
                self.posts.append(post)
    
    # check if we have already replied to the post
    def hasReplied(self, post):
        comments = post.comments.list()
        self.log(f"pulling comments list from: {post.url}")

        for comment in comments:
            if comment.author.name == config.redditInfo["username"]:
                self.log("already replied to this thread")
                return True

        self.log("never replied to this post")
        return False

    # download image
    def downloadPosts(self):
        for post in self.posts:
            self.log(f"downloading: {post.url}")
            os.system("wget -P ~/project/pizza/posts " + post.url)
    
    # get objects from image
    def getObjects(self, image_file_name):
        self.log(f"running image detection on image: {image_file_name}")
        return self.detector.detectObjectsFromImage(input_image=os.path.join(os.getcwd() , f"posts/{image_file_name}"),output_image_path=os.path.join(os.getcwd() , "garbage.jpg"))

    # check if pizza
    def checkForPizza(self, objects):
        for object_ in objects:
            if object_["name"] is "pizza":
                self.log("found pizza in image")
                return True
        self.log("no pizza found :(")
        return False
    
    def getImagePaths(self):
        return os.listdir(os.path.join(os.getcwd(), "posts/"))

    # randomize response
    def randomResponse(self):
        self.log("randomizing response")
        return random.choice(config.responses)

    # post to reddit thread
    def respondToPost(self, post, response):
        self.log(f"replying to post: {post} \n\t\twith response: {response}")
        post.reply(response)

    def addBotInfo(self):
        return"\n\n^^^(This is a bot, learn more about it [here](https://github.com/jeremy-laier/pizzabot))"
    
    # "main"
    def kickOff(self):
        self.fetchPosts()
        self.downloadPosts()

        for post, imagePath in zip(self.posts, self.getImagePaths()):
            objects = self.getObjects(imagePath)
            if self.checkForPizza(objects):
                self.respondToPost(post, self.randomResponse() + self.addBotInfo())

        self.cleanDir()

    # super basic logger for debugging during development
    def log(self, msg):
        if self.debug:
            print("***INFO***", msg)

    # delete the downloaded images
    def cleanDir(self):
        self.log(f"cleaning up possible downloaded images")
        files = os.listdir(os.path.join(os.getcwd(), "posts/"))
        for file_ in files:
            self.log(f"removing: {file_}")
            os.remove((os.path.join(os.getcwd(), f"posts/{file_}")))

        # remove output file from object detection 
        try:      
            os.remove((os.path.join(os.getcwd(), "garbage.jpg")))
        except:
            self.log("never processed any images to delete")

PizzaPoster("test_pizzasBoi", True).kickOff()
