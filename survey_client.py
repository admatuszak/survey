# Survey client tool 
from surveyor import *
import shelve
import streamlit as st
from sessionstate import get_state  # Assuming sessionstate.py lives on this folder
import pandas as pd
from dataclasses import dataclass
import time
from datetime import datetime, date, time, timezone
import altair as alt
import uuid


file = 'survey_db.pkl'
date_format = '%m/%d/%Y'
time_format = '%m/%d/%Y %I:%M %p'


def main():
    st.title("Monika's Prentice Survey Tool")
    st.sidebar.header("Main Menu")
    
    session = get_state(setup)
    #Need to figure out how to prevent __init__ from getting called every time an element is updated
    survey_instance = Survey_Instance(session)
    create_actions(survey_instance, session)
       
def create_actions(survey_instance, session):
    main_menu = st.sidebar.selectbox('Choose from actions below', 
                                     ['Administer New Survey', 'Load Completed Survey', 'Reporting']) 
    if main_menu== 'Reporting':
        st.write('Placeholder for analysis tab')
    elif main_menu == 'Load Completed Survey':
        #Maybe this shouldn't be in the same class as survey_instance
        db_instance = Survey_Instance(session)
        db_instance.open_survey_db()
        
        db = db_instance.survey_db
        
        #Need to build in try to catch errors on opening the file
        st.write('Number of Surveys Loaded from Database: ', db['Survey ID'].nunique())
        
        list_of_filter_options = ['Student', 'Date Administered', 'Teacher', 'Subject', 'Grade']
        
        filters = st.multiselect('Choose filters to apply. Click to add additional filter types', list_of_filter_options, default=list_of_filter_options)
        condition = [True for x in range(len(db))]
        
        if 'Student' in filters:
            student = select_student_to_load(db)
            condition = condition & (db['Student'] == student)
        if 'Date Administered' in filters:
            date = select_date_to_load(db, condition)
            condition = condition & (db['Date Administered'].dt.strftime(date_format) == date)
        if 'Teacher' in filters:
            teacher = select_teacher_to_load(db, condition)
            condition = condition & (db['Teacher'] == teacher)
        if 'Subject' in filters:
            subject = select_subject_to_load(db, condition)
            condition = condition & (db['Subject'] == subject)
        if 'Grade' in filters:
            grade = select_grade_to_load(db, condition)
            condition = condition & (db['Grade'] == grade)
            
        returned_survey = db[condition]
        
        #Check to see if there is more than one unique survey based on the criteria
        if returned_survey['Survey ID'].nunique() > 1:
            st.warning('There was more than one survey returned based on these criteria. Please select one below.')
            time = select_time_to_load(returned_survey, condition)
            returned_survey = returned_survey.loc[returned_survey['Date Administered'].dt.strftime(time_format) == time]

        st.header('Survey Results for ' + str(returned_survey['Student'].unique()[0]))
        st.text('Administered on ' + str(returned_survey['Date Administered'].dt.strftime(date_format).unique()[0]))
        
        st.write('\n\n\n\n\n')
        
        returned_survey.index = range(1,len(returned_survey)+1)
        st.write(returned_survey[['Category', 'Question', 'Answer']])
        
        st.write('\n\n\n\n\n')
        
        bar = alt.Chart(returned_survey).mark_bar().encode(
            alt.X('Answer', axis=alt.Axis(tickMinStep=1),scale=alt.Scale(domain=(0,5))),
            alt.Y('Question'),
            color=alt.Color('Category', scale=alt.Scale(scheme='category20c'))
        ).properties(
            title='Survey Question and Answers',
            width=600
        )
        
        st.altair_chart(bar)
        
        group = returned_survey[['Category','Answer']].groupby('Category').agg(['sum', 'count'])
        group.columns = group.columns.get_level_values(1)
        
        group['Max Possible Score'] = group['count'] * 5
        group['Percent of Total Possible Score'] = group['sum'] / group ['Max Possible Score']
        
        st.write('\n\n\n\n\n')
        
        chart_score_possible = alt.Chart(group.reset_index()).mark_bar().encode(
            alt.X('Category'),
            alt.Y('Percent of Total Possible Score', axis=alt.Axis(format='.0%', title='% of Total Possible Score'), scale=alt.Scale(domain=(0,1))),
            color=alt.Color('Category', scale=alt.Scale(scheme='category20c'))
        ).properties(
            title='Score as % of Total Possible, by Category',
            width=600,
            height=400
        )
        
        text = chart_score_possible.mark_text(
            align='center',
            baseline='top',
            dy=-15
        ).encode(
            text=alt.Text('Percent of Total Possible Score', format='.0%')
        ).transform_calculate()
        
        st.altair_chart(chart_score_possible + text)
        
        st.write(group['Percent of Total Possible Score'].map('{:.0%}'.format))
        comment_db = db_instance.open_comment_db()
        
        survey = str(returned_survey['Survey ID'].unique())
        st.write(str(survey))
        
        #except:
        #    st.error('There are no surveys to load. Choose Administer New Survey in the Main Menu to create one first.')
        
            
            
    elif main_menu == 'Administer New Survey':
        st.sidebar.subheader('Survey Actions')
        
        survey_instance.configure_survey()
        
        
        #Put reset button higher than create_survey function so that it overwrites the survey display with new session key
        if st.sidebar.button('Reset / New Survey'):
            survey_instance.new_survey()
        
        #Create and display the survey before the save_survey function so user can save work in progress without resetting
        st.write("Survey Version", survey_instance.version)
        survey_instance.create_survey()
        
        if st.sidebar.button('Save Survey'):
            survey_instance.save_survey()
        
        #This is just a shortcut for the session id, which sits in the survey_instance object
        session_key = survey_instance.session.session_id
                   
        if st.checkbox('Show the current survey details', key=session_key):
            survey_instance.show_survey()
        

def select_student_to_load(db):
    student = st.selectbox('Choose a student', db['Student'].unique())
    return student

def select_date_to_load(db, condition):
    date = st.selectbox('Choose the date of the survey', db['Date Administered'].loc[condition].dt.strftime(date_format).unique())
    return date

def select_time_to_load(db,condition):
    time = st.selectbox('Choose the time the survey was administered', db['Date Administered'].loc[condition].dt.strftime(time_format).unique())
    return time

def select_teacher_to_load(db, condition):
    teacher = st.selectbox('Choose the teacher', db['Teacher'].loc[condition].unique())
    return teacher

def select_subject_to_load(db, condition):
    grade = st.selectbox('Choose the subject', db['Subject'].loc[condition].unique())
    return grade

def select_grade_to_load(db, condition):
    grade = st.selectbox('Choose the grade', db['Grade'].loc[condition].unique())
    return grade
        
            
def run_analysis():
    data_instance = Data_Instance()
    return data_instance

def open_survey_db():
    try:
        surveys = pd.read_pickle(file)
    except:
        st.error("No survey data exists yet. Please complete your first survey or import surveys first.")
    else:
        return surveys
    

@dataclass
class MyState:
    session_id: int
    survey_id: hex

def setup() -> MyState:
    print('Running setup')
    return MyState(session_id=0, survey_id=str(uuid.uuid4()))





        
class Data_Instance():
    def __init__(self):
        #self.session = SessionState.get(run_id=0)
        self.data = open_survey_db()
    
    def show_all_data(self):
        st.write(self.data)
    
    def select_questions(self):
        self.selected_questions = st.multiselect('Pick the questions to include in analysis', self.data['Question'].unique(), key=self.session.run_id)
    
    def groupby_categories(self):
        total_questions_per_cat_dict = {cat:len(surveys['Question'].loc[surveys['Category'] == cat].unique()) for cat in surveys['Category'].unique()}
        

##### Initiate 
if __name__ == "__main__":
    
    main()
    
    
        
     

    
    