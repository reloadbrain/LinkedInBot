#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, random, sys, time, urlparse
from selenium import webdriver
from bs4 import BeautifulSoup
from random import shuffle

# Configurable Constants
EMAIL = 'youremail@gmail.com'
PASSWORD = 'password'
VIEW_SPECIFIC_USERS = False
SPECIFIC_USERS_TO_VIEW = ['CEO', 'CTO', 'Developer', 'HR', 'Recruiter']
NUM_LAZY_LOAD_ON_MY_NETWORK_PAGE = 5
CONNECT_WITH_USERS = True
JOBS_TO_CONNECT_WITH = ['CEO', 'CTO', 'Developer', 'HR', 'Recruiter']
VERBOSE = True

def Launch():
    """
    Launch the LinkedIn bot.
    """

    # Check if the file 'visitedUsers.txt' exists, otherwise create it
    if os.path.isfile('visitedUsers.txt') == False:
        visitedUsersFile = open('visitedUsers.txt', 'wb')
        visitedUsersFile.close()

    # Browser choice
    print 'Choose your browser:'
    print '[1] Chrome'
    print '[2] Firefox/Iceweasel'
    print '[3] PhantomJS'

    while True:
        try:
            browserChoice = int(raw_input('Choice? '))
        except ValueError:
            print 'Invalid choice.',
        else:
            if browserChoice not in [1,2,3]:
                print 'Invalid choice.',
            else:
                break

    StartBrowser(browserChoice)

def StartBrowser(browserChoice):
    """
    Launch broswer based on the user's selected choice.
    browserChoice: the browser selected by the user.
    """

    if browserChoice == 1:
        print '\nLaunching Chrome'
        browser = webdriver.Chrome()

    elif browserChoice == 2:
        print '\nLaunching Firefox/Iceweasel'
        browser = webdriver.Firefox()

    elif browserChoice == 3:
        print '\nLaunching PhantomJS'
        browser = webdriver.PhantomJS()

    # Sign in
    browser.get('https://linkedin.com/uas/login')
    emailElement = browser.find_element_by_id('session_key-login')
    emailElement.send_keys(EMAIL)
    passElement = browser.find_element_by_id('session_password-login')
    passElement.send_keys(PASSWORD)
    passElement.submit()

    print 'Signing in...'
    time.sleep(3)

    soup = BeautifulSoup(browser.page_source, "lxml")
    if soup.find('div', {'class':'alert error'}):
        print 'Error! Please verify your username and password.'
        browser.quit()
    elif browser.title == '403: Forbidden':
        print 'LinkedIn is momentarily unavailable. Please wait a moment, then try again.'
        browser.quit()
    else:
        print 'Success!\n'
        LinkedInBot(browser)


def LinkedInBot(browser):
    """
    Run the LinkedIn Bot.
    browser: the selenium driver to run the bot with.
    """

    T = 0
    V = 0
    profilesQueued = []
    error403Count = 0
    timer = time.time()

    print 'At the my network page to scrape user urls..\n'

    # Infinite loop
    while True:

        # Generate random IDs
        while True:

            NavigateToMyNetworkPage(browser)
            T += 1

            if GetNewProfileURLS(BeautifulSoup(browser.page_source, "lxml"), profilesQueued):
                break
            else:
                print '|',
                time.sleep(random.uniform(5, 7))

        soup = BeautifulSoup(browser.page_source, "lxml")
        profilesQueued = list(set(GetNewProfileURLS(soup, profilesQueued)))

        V += 1
        print '\n\nGot our users to start viewing with!\n'
        print browser.title.replace(' | LinkedIn', ''), ' visited. T:', T, '| V:', V, '| Q:', len(profilesQueued)

        while profilesQueued:

            shuffle(profilesQueued)
            profileID = profilesQueued.pop()
            browser.get('https://www.linkedin.com'+profileID)

            # Connect with users if the flag is turned on and matches your criteria
            if CONNECT_WITH_USERS:
                ConnectWithUser(browser)

            # Add the ID to the visitedUsersFile
            with open('visitedUsers.txt', 'ab') as visitedUsersFile:
                visitedUsersFile.write(str(profileID)+'\r\n')
            visitedUsersFile.close()

            # Get new profiles ID
            time.sleep(10)
            soup = BeautifulSoup(browser.page_source, "lxml")
            profilesQueued.extend(GetNewProfileURLS(soup, profilesQueued))
            profilesQueued = list(set(profilesQueued))

            browserTitle = (browser.title).encode('ascii', 'ignore').replace('  ',' ')

            # 403 error
            if browserTitle == '403: Forbidden':
                error403Count += 1
                print '\nLinkedIn is momentarily unavailable - Paused for', str(error403Count), 'hour(s)\n'
                time.sleep(3600*error403Count+(random.randrange(0, 10))*60)
                timer = time.time() # Reset the timer

            # User out of network
            elif browserTitle == 'Profile | LinkedIn':
                T += 1
                error403Count = 0
                print 'User not in your network. T:', T, '| V:', V, '| Q:', len(profilesQueued)

            # User in network
            else:
                T += 1
                V += 1
                error403Count = 0
                print browserTitle.replace(' | LinkedIn', ''), 'visited. T:', T, '| V:', V, '| Q:', len(profilesQueued)

            # Pause
            if (T%1000==0) or time.time()-timer > 3600:
                print '\nPaused for 1 hour\n'
                time.sleep(3600+(random.randrange(0, 10))*60)
                timer = time.time() # Reset the timer
            else:
                time.sleep(random.uniform(5, 7)) # Otherwise, sleep to make sure everything loads

        print '\nNo more profiles to visit. Everything restarts with the network page...\n'


def NavigateToMyNetworkPage(browser):
    """
    Navigate to the my network page and scroll to the bottom and let the lazy loading
    go to be able to grab more potential users in your network. It is reccommended to
    increase the NUM_LAZY_LOAD_ON_MY_NETWORK_PAGE value if you are using the variable
    SPECIFIC_USERS_TO_VIEW.
    browser: the selenium browser used to interact with the page.
    """

    browser.get('https://www.linkedin.com/mynetwork/')
    for counter in range(1,NUM_LAZY_LOAD_ON_MY_NETWORK_PAGE):
        ScrollToBottomAndWaitForLoad(browser)


def ConnectWithUser(browser):
    """
    Connect with the user viewing if their job title is found in your list of roles
    you want to connect with.
    browse: the selenium browser used to interact with the page.
    """

    soup = BeautifulSoup(browser.page_source, "lxml")
    jobTitleMatches = False

    # I know not that efficient of a loop but BeautifulSoup and Selenium are
    # giving me a hard time finding the specifc h2 element that contain's user's job title
    for h2 in soup.find_all('h2'):
        for job in JOBS_TO_CONNECT_WITH:
            if job in h2.getText():
                jobTitleMatches = True
                break

    if jobTitleMatches:
        try:
            if VERBOSE:
                print 'Sending the user an invitation to connect.'
            browser.find_element_by_xpath('//button[@class="connect primary top-card-action ember-view"]').click()
            browser.find_element_by_xpath('//button[@class="button-primary-large ml3"]').click()
        except:
            print 'Could not connect with the user due to an exception thrown.'
            pass


def GetNewProfileURLS(soup, profilesQueued):

    """
    Get new profile urls to add to the navigate queue.
    soup: beautiful soup instance of page's source code.
    profileQueued: current list of profile queues.
    """

    # Open, load and close
    with open('visitedUsers.txt', 'r') as visitedUsersFile:
        visitedUsers = [line.strip() for line in visitedUsersFile]
    visitedUsersFile.close()

    # Get profiles from the "People Also Viewed" section
    profileURLS = []

    # TODO: This portion needs to be cleaned up. It's pretty ugly at the moment.
    try:
        for a in soup.find_all('a', class_='mn-person-info__link'):
            if ValidateURL(a['href'], profileURLS, profilesQueued, visitedUsers):

                if VIEW_SPECIFIC_USERS:
                    for span in a.find_all('span', class_='mn-person-info__occupation'):
                        for occupation in SPECIFIC_USERS_TO_VIEW:
                            if occupation.lower() in span.text.lower():
                                if VERBOSE:
                                    print a['href']
                                profileURLS.append(a['href'])
                                break

                else:
                    if VERBOSE:
                        print a['href']
                    profileURLS.append(a['href'])
    except:
        pass

    try:
        for a in soup.find_all('a', class_='pv-browsemap-section__member'):
            if ValidateURL(a['href'], profileURLS, profilesQueued, visitedUsers):

                if VIEW_SPECIFIC_USERS:
                    for div in a.find_all('div'):
                        for occupation in SPECIFIC_USERS_TO_VIEW:
                            if occupation.lower() in div.text.lower():
                                if VERBOSE:
                                    print a['href']
                                profileURLS.append(a['href'])
                                break

                else:
                    if VERBOSE:
                        print a['href']
                    profileURLS.append(a['href'])
    except:
        pass

    try:
        for ul in soup.find_all('ul', class_='pv-profile-section__section-info'):
            for li in ul.find_all('li'):
                a = li.find('a')
                if ValidateURL(a['href'], profileURLS, profilesQueued, visitedUsers):

                    if VIEW_SPECIFIC_USERS:
                        for div in a.find_all('div'):
                            for occupatio in SPECIFIC_USERS_TO_VIEW:
                                if occupation.lower() in div.text.lower():
                                    if VERBOSE:
                                        print a['href']
                                    profileURLS.append(a['href'])
                                    break

                    else:
                        if VERBOSE:
                            print a['href']
                        profileURLS.append(a['href'])
    except:
        pass

    profileURLS = list(set(profileURLS))
    return profileURLS


def ValidateURL(url, profileURLS, profilesQueued, visitedUsers):
    """
    Validate the url passed meets requirement to be navigated to.
    profileURLS: list of urls already added within the GetNewProfileURLS method to be returned.
        Want to make sure we are not adding duplicates.
    profilesQueued: list of urls already added and being looped. Want to make sure we are not
        adding duplicates.
    visitedUsers: users already visited. Don't want to be creepy and visit them multiple days in a row.
    """

    return url not in profileURLS and url not in profilesQueued and "/in/" in url and "connections" not in url and "skills" not in url and url not in visitedUsers


def ScrollToBottomAndWaitForLoad(browser):
    """
    Scroll to the bottom of the page and wait for the page to perform it's lazy laoding.
    browser: selenium webdriver used to interact with the browser.
    """

    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)


if __name__ == '__main__':
    Launch()
