
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

class Client:

    def __init__(self):
        self.name = inquirer.text(message='What is your name?').execute()
        self.Menu()


    def Menu(self):

        x = True

        while x == True:
            main_menu = inquirer.select(
                message='Welcome to newsHub',
                choices=[
                    'Find new subject',
                    'Open subjects',
                    Choice(value=None, name='Exit'),
                ],
                default=1,
            ).execute()

            if main_menu == 'Find new subject':
                self.NewSubject()
            elif main_menu == 'Open subjects':
                self.OpenSubjects()
            elif main_menu == None:
                x = False

    def OpenSubjects(self):

        newList = self.GetOpenNews()
        newList.append('Return main menu')
        
        y = True

        while y == True:
            subject_list = inquirer.select(
                message='Open subjects',
                choices=newList,
                default=1
            ).execute()

            if subject_list == 'Return main menu':
                y = False
            else:
                print(subject_list)

    def GetOpenNews(self):
        ## NewsList where open chats from database
        tags_list2 = ['marjamehu', 'osakkeet', 'mustikka']

        return tags_list2
    
    def NewSubject(self):

        new_subject = inquirer.text(message='Find new subject').execute(),                
        print(new_subject)

        ## push subject to database open chatroom


if __name__ == '__main__':
    Client()
