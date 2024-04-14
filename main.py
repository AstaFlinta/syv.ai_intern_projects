from helium import *
from bs4 import BeautifulSoup
import chromadb

"""
Det her er en webscraper, som kan ekstrahere kommentarer og metadata fra et LinkedIn post.

Du skal selv give scriptet en url, username og password.

For at køre skal du have internetforbindelse, installeret firefox og importeret de følgende moduler:

from helium import *
from bs4 import BeautifulSoup
import chromadb

"""

class Linkedin_Scraper:
    def __init__(self, url, username, password):
        """
        :param url: a string containing the url where the comments should be loaded from
        :param username: a string containing the username used for login
        :param password: a string containing the password used for login
        """
        self.url = url
        self.username = username
        self.password = password
        self.driver = self.get_to_page()
        self.comment_info = self.get_comments()

    def unfold_see_more(self):
        """
        Unfolds all comments so all text is reachable
        """
        while len(find_all(
                Button("see more, visually reveals content which is already detected by screen readers"))) != 0:
            try: # this is really slow - too slow?
                click(Button("see more, visually reveals content which is already detected by screen readers"))
            except:
                scroll_down(500) # 500 just to speed it up a bit


    def get_to_page(self):
        """
        Method starts the browser, logs in, and navigates to the url
        :return: The driver (object?)
        """

        # opening up the login page in firefox
        try:
            self.driver = start_firefox('linkedin.com/login')
        except:
            SystemError("Is your wifi on? Do you have firefox installed?")

        # inputting username and password, checking that strings are being passed
        if not isinstance(self.password, str):
            raise TypeError("the password entered must be a string")
        if not isinstance(self.username, str):
            raise TypeError("the username entered must be a string")

        write(self.username, into='Email or Phone')
        write(self.password, into='Password')
        click('Sign in')

        # Error message if login doesn't go through
        if Text("Wrong email or password. Try again or create an account").exists():
            raise ValueError("Did you input the wrong username or password?")


        # just waiting for the sign in to go through before I move on
        # also adds a 60 second timeout for you to manually clear possible verification tasks
        wait_until(Text("Start a post").exists, timeout_secs = 60)

        if not isinstance(self.url, str):
            raise TypeError("the url entered must be a string")
        go_to(self.url)
        if Text("Please check your URL or return to LinkedIn home.").exists():
            raise ValueError("That url doesn't seem to go anywhere. Are you sure it is correct?")

        # call method to unfold the comment text
        self.unfold_see_more()

        return self.driver

    def get_comments(self):

        """
        Method retrieves the comments as well as metadata (author and time stamp)
        :return: a list of lists with the comment, author, and time stamp in order
        """

        # accessing the source code in a legibel way
        page_source = self.driver.page_source
        doc = BeautifulSoup(page_source, 'html.parser')

        # finding the tags for each comment, author, and timestamp
        comment_tags = doc.select(
            "div.comments-comment-item__inline-show-more-text.feed-shared-inline-show-more-text")
        author_tags = doc.select(
            "span.comments-post-meta__name.text-body-small-open.t-black > span.comments-post-meta__name-text.t-14.hoverable-link-text")
        time_tags = doc.select("div.comments-comment-item__options > time")

        # just checking that the three tag lists above should be equally long or something has gone wrong
        if len(comment_tags) != len(author_tags) != len(time_tags):
            raise ValueError("You are missing a tag. Something went wrong!")

        # making the list of lists
        comment_info_raw = []
        for i in range(len(comment_tags)):
            comment_info_raw.append(
                [comment_tags[i].text.strip(), time_tags[i].text.strip(), author_tags[i].text.strip()])

        # just getting rid of potential duplicates
        self.comment_info = []
        [self.comment_info.append(x) for x in comment_info_raw if x not in self.comment_info]

        return self.comment_info

    def vector_database(self):
        """
        Method uploads the comment_info in a vector database
        :return: the collection (object?)
        """

        chroma_client = chromadb.Client()
        self.collection = chroma_client.create_collection(name="syv_ai_junior_comments")
        for i in range(len(self.comment_info)):
            self.collection.add(documents=self.comment_info[i][0],
                                ids="id" + str(i),
                                metadatas={"time_and_author": self.comment_info[i][1] + ", " + self.comment_info[i][2]})
        # not sure if this is the best way to store the metadatas, can you store them seperately?

        print(self.comment_info)
        return self.collection
