from datetime import datetime, date, time, timezone
from passlib.apps import custom_app_context as pwd_context
import shelve
import pandas as pd
import pickle
import uuid
import streamlit as st
import time

class User():
    user_directory_file = 'user_directory.pkl'
    
    def __init__(self):
        open_user_directory()
        self.auth_status=False
        self.auth_user_uuid=''
        self.auth_user_name=''
        
    def open_user_directory(self):
        try:
            with open(self.user_directory_file, 'rb') as handle:
                self.user_directory = pickle.load(handle)
        except:
            self.display('There was an error opening the user directory.', type='error')
    
    def authenticate_user(self):
        self.get_user_selectbox(role_match='no', text_to_display='Please choose your name below')
        self.password_provided = st.text_input('Please enter your password below')
        self.check_password()
        
    #Need to account for the fact that unauthenticated user doesn't have a role
    def get_user_selectbox(self, role_match='yes', text_to_display='Please Choose the User Below'):
        if role_match == 'yes':
            option = self.user_directory['UUID'].loc[self.user_directory['Role'] == self.user_role]
        else:
            option = self.user_directory['UUID']
        format_string = lambda i: ' '.join(self.user_directory[['First Name', 'Last Name']].loc[self.user_directory['UUID'] == i].values[0])
        self.selected_uuid = st.selectbox(text_to_display,
                                          options=list(option),
                                          format_func=format_string)
    def check_password(self):
        password_hash = self.user_directory['Password Hash'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0]
        password_check = pwd_context.verify(self.password_provided, password_hash)
        if password_check == True:
            self.display('You are now authenticated. Please pick from an action in the main menu to the left.')
            self.auth_status=True
            self.auth_user_uuid=self.selected_uuid
            self.auth_user_name=self.uuid_to_name(self.auth_user_uuid)
        elif self.password_provided == '':
            pass
        else:
            st.error('Your password is not correct')
            self.auth_status=False
            self.user=''
                        
    def list_users_from_directory(self):
        self.user_directory.reindex()
        self.display('The following is a list of current users and their roles.')
        self.display(self.user_directory[['Title', 'First Name','Last Name','Role']])             
    
    def add_user(self):
        user_id = uuid.uuid4().int
        first_name = st.text_input('First Name')
        last_name = st.text_input('Last Name')
        title = st.text_input('Title, e.g., Mr. or Mrs.')
        password = st.text_input('Type the password for this user.')
        user_role = st.selectbox('Choose the role for the user', ['Student', 'Teacher', 'Admin'])
        password_hash = pwd_context.hash(password)
        user_to_add = [(user_id, title, first_name, last_name, password_hash, user_class)]
        self.commit_user(user_to_add)

    def delete_user(self):
        self.display('Please select the user below to delete.')
        self.get_user_selectbox(role_match='no', text_to_display='Choose User to Delete')
        confirm = st.text_input('Type Yes to confirm deletion')
        if self.selected_uuid == self.auth_user_uuid:
            self.display('You may not delete your own user', type='error')
        elif confirm == 'Yes':
            self.user_directory.drop(self.user_directory[self.user_directory['UUID'] == self.selected_uuid].index, inplace=True)
            self.display('The user has been deleted', type='success')
            self.save_user_directory(animation='no')
        elif confirm == '':
            pass
        else:
            self.display('The user has not been deleted', type='error')
            
    def reset_user(self):
        self.get_user_selectbox(role_match='no', text_to_display='Choose the User to Reset')
        selected_user_role = self.user_directory['Role'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0]
        if selected_user_role == 'Student':
            index_for_role = 0
        elif selected_user_role == 'Teacher':
            index_for_role = 1
        else:
            index_for_role = 2
        uuid = self.selected_uuid
        password = st.text_input('Type the NEW password for this user below')
        password_hash = pwd_context.hash(password)
        first_name = st.text_input('First Name', value=self.user_directory['First Name'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        last_name = st.text_input('Last Name', value=self.user_directory['Last Name'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        title = st.text_input('Title, e.g., Mr. or Mrs.', value=self.user_directory['Title'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        role = st.selectbox('Choose the role for the user', ['Student', 'Teacher', 'Admin'], index=index_for_role)
        self.user_to_update = [(uuid, title, first_name, last_name, password_hash, role)]
        #need to build in commit
                                          
    def commit_user(self, user_to_add):
        if st.button('Commit Changes'):
            self.add_user_to_directory(user_to_add)
            self.save_user_directory()
            
    def add_user_to_directory(self, user_to_add):
        directory_columns = self.user_directory.columns
        new_data_frame = pd.DataFrame(user_to_add, columns=directory_columns)
        self.user_directory = self.user_directory.append(new_data_frame, ignore_index=True)
                                          
    def save_user_directory(self, animation='yes'):
        with open(self.user_directory_file, 'wb') as handle:
            pickle.dump(self.user_directory, handle, protocol=pickle.HIGHEST_PROTOCOL)
        if animation=='yes':
            st.balloons()
                                          
    def uuid_to_name(self, uuid):
        full_name = ' '.join(self.user_directory[['First Name', 'Last Name']].loc[self.user_directory['UUID'] == uuid].values[0])
        return full_name
                                          
    def display(self, text, type='text'):
        if type=='text':
            st.write(text)
        elif type=='error':
            st.error(text)
        elif type=='success':
            st.success(text)

class Survey_Instance():
    version = .02
    config_file = 'config'
    survey_db = 'survey_db.pkl'
    comment_db = 'comment_db.pkl'
    user_directory_file = 'user_directory.pkl'
    
    def __init__(self, session):
        self.session = session
    
    
    ##### User Administration #####
    def authenticate(self):
        self.open_user_directory() ## See if we can add function to check instead of having to call this function so much
        self.get_user_selectbox(text_to_display='Choose Your Name Below')
        self.password_provided = st.text_input('Please enter your password below')
        self.check_password()
        
    def get_user_selectbox(self, role_match='yes', text_to_display='Please Choose the User Below'):
        self.open_user_directory()
        if role_match == 'yes':
            option = self.user_directory['UUID'].loc[self.user_directory['Role'] == self.session.user_class]
        else:
            option = self.user_directory['UUID']
        format_string = lambda i: ' '.join(self.user_directory[['First Name', 'Last Name']].loc[self.user_directory['UUID'] == i].values[0])
        self.selected_uuid = st.selectbox(text_to_display,
                                          options=list(option),
                                          format_func=format_string)

    def check_password(self):
        self.open_user_directory()
        password_hash = self.user_directory['Password Hash'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0]
        password_check = pwd_context.verify(self.password_provided, password_hash)
        if password_check == True:
            st.success('You are now authenticated. Please pick from an action in the main menu to the left.')
            self.session.auth_status=True
            self.session.user=self.selected_uuid
        elif self.password_provided == '':
            pass
        else:
            st.error('Your password is not correct')
            self.session.auth_status=False
            self.session.user=''
    
    def uuid_to_name(self, uuid):
        self.open_user_directory()
        full_name = ' '.join(self.user_directory[['First Name', 'Last Name']].loc[self.user_directory['UUID'] == uuid].values[0])
        return full_name
    
    def list_users_from_directory(self):
        self.open_user_directory()
        self.user_directory.reindex()
        st.write('The following is a list of current users and their roles.')
        st.write(self.user_directory[['Title', 'First Name','Last Name','Role']])
        
    def add_user(self):
        user_id = uuid.uuid4().int
        first_name = st.text_input('First Name')
        last_name = st.text_input('Last Name')
        title = st.text_input('Title, e.g., Mr. or Mrs.')
        password = st.text_input('Type the password for this user.')
        user_class = st.selectbox('Choose the role for the user', ['Student', 'Teacher', 'Admin'])
        password_hash = pwd_context.hash(password)
        self.user_to_add = [(user_id, title, first_name, last_name, password_hash, user_class)]
        self.commit_user()
        
    def delete_user(self):
        st.write('Please select the user below to delete.')
        self.get_user_selectbox(role_match='no', text_to_display='Choose User to Delete')
        confirm = st.text_input('Type Yes to confirm deletion')
        if self.selected_uuid == self.session.user:
            st.error('You may not delete your own user')
        elif confirm == 'Yes':
            self.user_directory.drop(self.user_directory[self.user_directory['UUID'] == self.selected_uuid].index, inplace=True)
            st.success('The user has been deleted')
            self.save_user_directory(animation='no')
        elif confirm == '':
            pass
        else:
            st.error('The user has not been deleted')
            
    def reset_user(self):
        self.get_user_selectbox(role_match='no', text_to_display='Choose the User to Reset')
        selected_user_role = self.user_directory['Role'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0]
        if selected_user_role == 'Student':
            index_for_role = 0
        elif selected_user_role == 'Teacher':
            index_for_role = 1
        else:
            index_for_role = 2
        uuid = self.selected_uuid
        password = st.text_input('Type the NEW password for this user below')
        password_hash = pwd_context.hash(password)
        first_name = st.text_input('First Name', value=self.user_directory['First Name'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        last_name = st.text_input('Last Name', value=self.user_directory['Last Name'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        title = st.text_input('Title, e.g., Mr. or Mrs.', value=self.user_directory['Title'].loc[self.user_directory['UUID'] == self.selected_uuid].values[0])
        role = st.selectbox('Choose the role for the user', ['Student', 'Teacher', 'Admin'], index=index_for_role)
        self.user_to_update = [(uuid, title, first_name, last_name, password_hash, role)]
        
        
    def commit_user(self):
        if st.button('Commit Changes'):
            self.open_user_directory()
            self.add_user_to_directory(self.user_to_add)
            self.save_user_directory()
            
    def add_user_to_directory(self, user_list):
        directory_columns = self.user_directory.columns
        new_data_frame = pd.DataFrame(user_list, columns=directory_columns)
        self.user_directory = self.user_directory.append(new_data_frame, ignore_index=True)
    
    def update_user_in_directory(self, user_list):
        directory_columns = self.user_directory.columns
        self.user_directory['Title', 'First Name', 'Last Name', 'Password Hash', 'Role']\
            .loc[self.user_directory['UUID'] == user_list[uuid]] = user_list['title', 'first_name', 'last_name', 'password_hash', 'role']
    
    def open_user_directory(self):
        try:
            with open(self.user_directory_file, 'rb') as handle:
                self.user_directory = pickle.load(handle)
        except:
            st.error('There was an error opening user directory')
    
    def save_user_directory(self):
        with open(self.user_directory_file, 'wb') as handle:
                pickle.dump(self.user_directory, handle, protocol=pickle.HIGHEST_PROTOCOL)
        st.balloons()
    
    ##### End of User Administration #####
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
        self.survey_answers['User'] = self.uuid_to_name(self.session.user)
        
        for question in self.survey_answers['Question'].items():
            print(question[1])
            self.survey_answers.at[question[0], 'Answer'] = st.slider(question[1], 1, 5, key=self.session.session_id)
            self.survey_answers.at[question[0], 'Date Administered'] = datetime.now()
        
        self.survey_comment = st.text_area('Please enter any comments for this survey below', key=self.session.session_id)
        self.comment = {self.session.survey_id:self.survey_comment}
        self.survey_answers['Survey ID'] = self.session.survey_id
        self.close_shelf()
    
    def save_survey(self, animation='yes'):
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
        if animation=='yes':
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
        try:
            username = self.uuid_to_name(self.session.user)
        except:
            username = 'Not logged in'
            
        st.sidebar.subheader('Status')
        st.sidebar.markdown('User: ' +  username)
        st.sidebar.markdown('User Class: *' + self.session.user_class + '*')
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
