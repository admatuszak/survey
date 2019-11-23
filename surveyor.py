from datetime import datetime, date, time, timezone
import shelve
import pandas as pd
import pickle
import uuid
import streamlit as st
import time

class Survey:
    version = .01
    
    def __init__(self):
        self.config_file = 'config_file'

    def printChoice(self, list_name, index):
        print(f"You choose: {list_name[index]}")
        return(list_name[index])
    
    def unpack_shelf(self):
        self.s = shelve.open(self.config_file)
        self.teacher_list = self.s['teacher_list']
        self.subject_list =  self.s['subject_list']
        self.student_list = self.s['student_list']
        self.question_list = self.s['question_list']
        self.s.close()
        
    def pack_shelf(self):
        self.s = shelve.open(self.config_file)
        self.s['teacher_list'] = self.teacher_list
        self.s['subject_list'] = self.subject_list
        self.s['student_list'] = self.student_list
        self.s['question_list'] = self.question_list
        self.s.close()
    
    @st.cache
    def configure_survey(self):
        self.unpack_shelf()
        
        print(f"Teacher Selection{'-'*30}")
        teacher_index = makeChoice(self.teacher_list)
        self.teacher = self.printChoice(self.teacher_list, teacher_index)
        print(f"\nSubject Selection{'-'*30}")
        subject_index = makeChoice(self.subject_list)
        self.subject = self.printChoice(self.subject_list, subject_index)
        print(f"\nStudent Selection{'-'*30}")
        student_index = makeChoice(self.student_list)
        self.student = self.printChoice(self.student_list, student_index)
        
        grade = ['Grade '+str(n) for n in range(1,13)]
        print(f"\nGrade Selection{'-'*30}")
        grade_index = makeChoice(grade)
        self.grade = self.printChoice(grade, grade_index)
        self.survey_questions = pd.DataFrame(self.question_list)
        self.survey_questions['Answer'] = ""
        self.survey_questions['Date Administered'] = ""
        
    def take_survey(self):
        
            
        print(f"\n\nPlease select a value 1 to 5 for the following questions")
        
        for question in self.survey_questions['Question'].items():
            print(question[1])
            answer = input('Answer: ')
            self.survey_questions.at[question[0], 'Answer'] = answer
            self.survey_questions.at[question[0], 'Date Administered'] = datetime.now()
        self.survey_questions['Student'] = self.student
        self.survey_questions['Teacher'] = self.teacher
        self.survey_questions['Subject'] = self.subject
        self.survey_questions['Grade'] = self.grade
        
        try:
            self.survey_db = pd.read_pickle('survey_db.pkl')
        except:
            self.survey_answers = self.survey_questions
        else:
            print("No error")
            self.survey_answers = self.survey_db.append(self.survey_questions)
        finally:
            self.survey_answers.to_pickle('survey_db.pkl')
        
            
    def display(self):
        print(f"\n\nStudent: {self.student} \t\tTeacher: {self.teacher} \t\tSubject: {self.subject}\n{self.grade}\n{'-'*30}")
        print(self.survey_questions)
        
    def groupby_categories(self):
        grp = self.list_of_questions.groupby('Category').size()


class Survey_Instance(Survey):
    def __init__(self, session):
        self.session = session
    
    def configure_survey(self):
        self.config_file = 'config_file'
        
        self.unpack_shelf()
        self.grade_list = ['Grade '+str(n) for n in range(1,13)]
        self.survey_questions = pd.DataFrame(self.question_list)
        self.survey_questions['Answer'] = ""
        self.survey_questions['Date Administered'] = ""
        
    def create_survey(self):
        st.write('In create_survey session ID: ', self.session.session_id)
        st.write('In create_survey survey ID:', self.session.survey_id)
        self.teacher = st.selectbox('Teacher', self.teacher_list, key=self.session.session_id)
        self.student = st.selectbox('Student', self.student_list, key=self.session.session_id)
        self.subject = st.selectbox('Subject', self.subject_list, key=self.session.session_id)
        self.grade = st.selectbox('Grade', self.grade_list, key=self.session.session_id)
        
        for question in self.survey_questions['Question'].items():
            print(question[1])
            self.survey_questions.at[question[0], 'Answer'] = st.slider(question[1], 1, 5, key=self.session.session_id)
            self.survey_questions.at[question[0], 'Date Administered'] = datetime.now()
        
        self.survey_comment = st.text_area('Please enter any comments for this survey below', key=self.session.session_id)
        self.comment = {self.session.survey_id:self.survey_comment}
        
        self.survey_questions['Teacher'] = self.teacher
        self.survey_questions['Student'] = self.student
        self.survey_questions['Subject'] = self.subject
        self.survey_questions['Grade'] = self.grade
        self.survey_questions['Survey ID'] = self.session.survey_id
    
    def save_survey(self):
        try:
            self.survey_db = pd.read_pickle('survey_db.pkl')
        except:
            self.survey_answers = self.survey_questions
        else:
            self.survey_answers = self.survey_db.append(self.survey_questions, ignore_index=True)
        finally:
            self.survey_answers.to_pickle('survey_db.pkl')
        
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
            
        st.balloons()
    
    
    def show_survey(self):
        st.write(self.survey_questions)
        
    def new_survey(self):
        self.session.session_id +=1
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
        self.comment = self.comment_db[self.survey_questions['Survey ID']]
        
    
    def survey_db_info(self):
        self.nunique_surveys = self.survey_db['Survey ID'].nunique()
        self.unique_surveys = self.survey_db['SurveyID'].unique()
   
import tkinter as tk

class SurveyGUI(tk.Tk):
    def __init__(self, teacher_list=None):
        super().__init__()
        
        if not teacher_list:
            self.teacher_list = []
        else:
            self.teacher_list = teacher_list
        
        self.teachers_canvas = tk.Canvas(self)
        self.teachers_frame = tk.Frame(self.teachers_canvas)
        self.text_frame = tk.Frame(self)
        
        self.scrollbar = tk.Scrollbar(self.teachers_canvas, orient="vertical", command=self.teachers_canvas.yview)

        self.teachers_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.title('Educational Survey Tool')
        self.geometry('300x400')
        self.label = tk.Label(self, text="Survey GUI", padx=5, pady=5)
        self.label.pack()
        
        list_of_teachers = tk.Label(self, text="Enter New Teacher if not Listed", pady=10)
        self.teacher_list.append(list_of_teachers)
        for teacher in self.teacher_list:
            print(teacher)
            teacher.pack(side=tk.TOP, fill=tk.X)

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
