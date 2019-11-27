from datetime import datetime, date, time, timezone
from passlib.apps import custom_app_context as pwd_context
import shelve
import pandas as pd
import pickle
import uuid
import streamlit as st
import time

class Survey_Instance():
    version = .02
    config_file = 'config'
    survey_db = 'survey_db.pkl'
    comment_db = 'comment_db.pkl'
    pass_db = 'pass.pkl'
    
    def __init__(self, session):
        self.session = session
    
    def authenticate(self):
        self.open_shelf()
        if self.session.user_class == 'Student':
            drop_down = 'student_list'
        elif self.session.user_class == 'Teacher':
            drop_down = 'teacher_list'
        self.selected_teacher = st.selectbox('Please choose your name below', self.shelf[drop_down])
        self.password = st.text_input('Please enter your password below')
        self.check_password()
        
    def check_password(self):
        self.open_pass_db()
        password_check = pwd_context.verify(self.password, self.loaded_passwords.get(self.selected_teacher))
        if password_check == True:
            st.success('You are now authenticated. Please pick from an action in the main menu to the left.')
            self.session.auth_status=True
            self.session.user=self.selected_teacher
        else:
            st.error('Your password is not correct')
            self.session.auth_status=False
            self.session.user='Not logged in'
    
    def open_pass_db(self):
        try:
            with open(self.pass_db, 'rb') as handle:
                self.loaded_passwords = pickle.load(handle)
        except:
            st.error('There was an error opening password db')
        finally:
            return self.loaded_passwords
    
    def add_user(self):
        user_id = uuid.uuid4().int
        user = st.text_input('Type the name of the user. E.g., Mr. Smith')
        password = st.text_input('Type the password for this user.')
        user_class = st.selectbox('Choose the role for the user', ['Student', 'Teacher', 'Admin'])
        password_hash = pwd_context.hash(password)
        user_list = ()
        
        ##left off
    
    def open_user_directory(self):
        try:
            with open(self.user_directory.pkl, 'rb') as handle:
                self.user_directory = pickle.load(handle)
        except:
            st.error('There was an error opening user directory')
    
    def add_user_to_directory(self, user_list):
        directory_columns = self.user_directory.columns
        new_data_frame = pd.DataFrame(user_list, columns=directory_columns)
        self.user_directory = self.user_directory.append(new_data_frame)
    
    def open_shelf(self):
        self.shelf = shelve.open(self.config_file)
        
    def close_shelf(self):
        self.shelf.close()
    
    def create_grade_list(self, start=0, end=12):
        self.grade_list = ['Grade ' + str(n) for n in range(start+1, end+1)]
    
    def create_survey(self):
        st.write('In create_survey session ID: ', self.session.session_id)
        st.write('In create_survey survey ID:', self.session.survey_id)
        st.write('In create_survey user class:', self.session.user_class)
        self.reset_button = st.empty()
        self.open_shelf()
        self.create_grade_list()
        self.survey_answers = pd.DataFrame(self.shelf['question_list'])
        self.survey_answers['Answer'] = ""
        self.survey_answers['Date Administered'] = ""
        self.survey_answers['Teacher'] = st.selectbox('Teacher', self.shelf['teacher_list'], key=self.session.session_id)
        self.survey_answers['Student'] = st.selectbox('Student', self.shelf['student_list'], key=self.session.session_id)
        self.survey_answers['Subject'] = st.selectbox('Subject', self.shelf['subject_list'], key=self.session.session_id)
        self.survey_answers['Grade'] = st.selectbox('Grade', self.grade_list, key=self.session.session_id)
        self.survey_answers['User'] = self.session.user
        
        for question in self.survey_answers['Question'].items():
            print(question[1])
            self.survey_answers.at[question[0], 'Answer'] = st.slider(question[1], 1, 5, key=self.session.session_id)
            self.survey_answers.at[question[0], 'Date Administered'] = datetime.now()
        
        self.survey_comment = st.text_area('Please enter any comments for this survey below', key=self.session.session_id)
        self.comment = {self.session.survey_id:self.survey_comment}
        self.survey_answers['Survey ID'] = self.session.survey_id
        self.close_shelf()
    
    def save_survey(self):
        try:
            self.survey_db = pd.read_pickle(self.survey_db)
        except:
            pass
        else:
            self.survey_answers = self.survey_db.append(self.survey_answers, ignore_index=True)
            self.session.saved_status=True
        finally:
            self.survey_answers.to_pickle(self.survey_db)
        self.save_comment()
        st.balloons()
        
    def saved_status(self):
        if self.session.saved_status == True: 
            self.saved_verb = 'has'
        else:
            self.saved_verb = 'has not'
        
    def save_comment(self):
        try:
            with open(self.comment_db, 'rb') as handle:
                self.comment_dictionary = pickle.load(handle)
        except:
            self.comment_dictionary = self.comment
        else:
            self.comment_dictionary[self.session.survey_id] = self.survey_comment
        finally:
            with open(self.comment_db, 'wb') as handle:
                pickle.dump(self.comment_dictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
    def show_survey(self):
        st.write(self.survey_answers)
        
    def new_survey(self):
        self.session.session_id +=1
        self.session.saved_status=False
        self.session.survey_id = str(uuid.uuid4())

    def provide_status(self, mode='base'):
        st.sidebar.subheader('Status')
        st.sidebar.markdown('User Class: *' + self.session.user_class + '*')
        st.sidebar.markdown('User: ' + self.session.user)
        st.sidebar.markdown('Authenticated: ' + str(self.session.auth_status))

        self.saved_status()
        if mode=='edit':
            st.sidebar.markdown('* You are **editing** the survey for '+self.survey_answers['Student'][0])
            st.sidebar.markdown('* The survey **'+self.saved_verb+'** been saved.')
            st.sidebar.markdown('* You may save the survey for *'+self.survey_answers['Student'][0]+ \
                                '* as many times as you would like. However, please remember to click the \
                                **Reset / New Survey** button above if you want to begin creating a new survey for another student.')
        
    def open_survey_db(self):
        try:
            self.survey_db = pd.read_pickle(self.survey_db)
        except:
            pass
        
    def open_comment_db(self):
        try:
            with open(self.comment_db, 'rb') as handle:
                self.comment_db = pickle.load(handle)
        except:
            self.comment_db = []
        finally:
            return self.comment_db
            
    def get_comment(self):
        self.comment = self.comment_db[self.survey_answers['Survey ID']]
        
    def survey_db_info(self):
        self.nunique_surveys = self.survey_db['Survey ID'].nunique()
        self.unique_surveys = self.survey_db['SurveyID'].unique()

if __name__ == "__main__":
    win = SurveyGUI()
    win.mainloop()
