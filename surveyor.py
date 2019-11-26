from datetime import datetime, date, time, timezone
import shelve
import pandas as pd
import pickle
import uuid
import streamlit as st
import time

class Survey_Instance():
    def __init__(self, session):
        self.version = .01
        self.session = session
        self.config_file = 'config'
    
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
            self.survey_db = pd.read_pickle('survey_db.pkl')
        except:
            pass
        else:
            self.survey_answers = self.survey_db.append(self.survey_answers, ignore_index=True)
            self.session.saved_status=True
        finally:
            self.survey_answers.to_pickle('survey_db.pkl')
        self.save_comment()
        st.balloons()
        
    def saved_status(self):
        if self.session.saved_status == True: 
            self.saved_verb = 'has'
        else:
            self.saved_verb = 'has not'
        
    def save_comment(self):
        try:
            with open('comment_db.pkl', 'rb') as handle:
                self.comment_dictionary = pickle.load(handle)
        except:
            self.comment_dictionary = self.comment
        else:
            self.comment_dictionary[self.session.survey_id] = self.survey_comment
        finally:
            with open('comment_db.pkl', 'wb') as handle:
                pickle.dump(self.comment_dictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
    def show_survey(self):
        st.write(self.survey_answers)
        
    def new_survey(self):
        self.session.session_id +=1
        self.session.saved_status=False
        self.session.survey_id = str(uuid.uuid4())

    def open_survey_db(self):
        try:
            self.survey_db = pd.read_pickle('survey_db.pkl')
        except:
            pass
        
    def open_comment_db(self):
        try:
            with open('comment_db.pkl', 'rb') as handle:
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

def makeChoice(list_of_choices):
    for x in range(len(list_of_choices)):
        print(f"{x+1}: {list_of_choices[x]}")
        
    answer = input("Please enter the number of your choice from above: ")
    try:
        answer = int(answer)-1
        if answer not in range(len(list_of_choices)):
            print("\nYou must select from above (you chose a number from outside the list)")
            return(makeChoice(list_of_choices))
    except ValueError:
        print("\nYou must enter a number")
        return(makeChoice(list_of_choices))
    return(answer)

if __name__ == "__main__":
    win = SurveyGUI()
    win.mainloop()
