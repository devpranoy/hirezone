from flask import Flask ,render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import dbquery
app = Flask(__name__)
@app.route('/')		#main route
def index():		#index page
	return render_template('index.html')
#===================Signup page===========================

@app.route('/signup',methods=['GET','POST'])
def signup():
	if request.method== 'POST': #retrieving values from user if POST
		name = request.form['name']
		email = request.form['email']
		password= request.form['password']
		sql="SELECT USERID FROM USERS WHERE EMAIL='%s'"%(email) #Security check on email
		try:
			rows = dbquery.fetchone(sql) #if none, error should be raised
			for row in rows:
				f=1
		except:
			sql="INSERT INTO USERS(NAME,EMAIL,PASSWORD) VALUES('%s','%s' ,'%s')"%(name,email,password)
			dbquery.inserttodb(sql)	#connecting to db model
			flash('You are now registered! Please Log in.','success') #sending a message to user
			return redirect( url_for('login')) #redirecting to login page
		flash('This Email exists!','success') #Checking for email
		return render_template('signup.html')
	return render_template('signup.html') # rendering the signup page

#====================Login page=========================

@app.route('/login', methods=['GET','POST']) #login page
def login():
	if request.method == 'POST':
		email = request.form['email']					#GET FORM FIELDS
		password_candidate= request.form['password']	#GET FORM FIELDS
		flag=0
		if email=='admin@mindhacks.com':
			if password_candidate=='adminadmin':
				session['logged_in'] = True
				session['name'] = 'Administrator'
				session['userid']='0'
				return render_template('admin_dash.html')


		sql="SELECT PASSWORD FROM USERS WHERE EMAIL= '%s' "%(email)
		rows = dbquery.fetchone(sql)
		try:				# if no entry found, an error is raised
			for row in rows:
				flag=1
				password=row
			sql="SELECT NAME FROM USERS WHERE EMAIL= '%s' "%(email)		#validations
			rows = dbquery.fetchone(sql)
			for row in rows:
				name=row
			sql="SELECT USERID FROM USERS WHERE EMAIL= '%s' "%(email)	#validations
			rows = dbquery.fetchone(sql)
			for row in rows:
				userid=row
			if str(password_candidate) == str(password):	#initialise session variable if passwords match
				session['logged_in'] = True
				session['name'] = str(name)
				session['userid']=userid
			else:
				error = 'Invalid login'
				return render_template('login.html',error=error)
		except:
			if flag==0:
				error = 'Email not found'
				return render_template('login.html',error=error)
		return redirect( url_for('dashboard'))#if verification is successful load the dashboard with session
	return render_template('login.html')

#-----------------------------------------SECURITY------------------------------

def is_logged_in(f):	# Function for implementing security and redirection
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorised, Please Login')
			return redirect(url_for('login'))
	return wrap	# A wrap is a concept that is used to check for authorisation of a request

#------------------------------- Dashboard -------------------------------------
@app.route('/dashboard.html',methods=['GET','POST'])
@is_logged_in						#Can only be accessed if logged in
def dashboard():
	usr=session['userid']	#Recieving the userid for db manipulation from the initilised session
	sql="SELECT * FROM PROJECTS WHERE USERID = %s"%(usr)
	projects=dbquery.fetchall(sql)
	return render_template('dashboard.html',projects=projects)

#------------------------------ Create a project -------------------------------
@app.route('/create' ,methods=['GET','POST'])
@is_logged_in
def create():
	if request.method == 'POST':
		title = request.form['title']	#GET FORM FIELDS
		description= request.form['description']	#GET FORM FIELDS
		sql="INSERT INTO PROJECTS(USERID,TITLE,DESCRIPTION,STATUS) VALUES(%s,'%s','%s','%s')"%(int(session['userid']),title,description,'PENDING VERIFICATION')
		dbquery.inserttodb(sql)
		flash('Project Created Successfully!','success')		#project successful
		return redirect( url_for('dashboard'))
	flash(' Submit a project !','success')
	return render_template('create.html')

#------------------ View created projects --------------------------------------

@app.route('/view', methods=['GET','POST'])
@is_logged_in
def view():
	usr=session['userid']	#Recieving the userid for db manipulation from the initilised session
	sql="SELECT * FROM PROJECTS WHERE USERID = %s"%(usr)
	projects=dbquery.fetchall(sql)
	return render_template('view.html',projects=projects)

#---------------------------------Dynamically creating projects pages-----------
@app.route('/projects/<string:id>',methods=['GET','POST'])
def projects(id):
	if request.method == 'POST':
		comment = request.form['comment']	#GET FORM FIELDS
		comment=str(comment)
		sql="INSERT INTO COMMENTS(PROJECTID,USERID,COMMENT) VALUES('%s','%s','%s')"%(id,int(session['userid']),comment)
		dbquery.inserttodb(sql)

	#GET requests
	usr=session['userid']
	sql="SELECT * FROM PROJECTS WHERE PROJECTID = %s"%(id)
	projects = dbquery.fetchall(sql)
	sql="SELECT * FROM COMMENTS WHERE PROJECTID = %s"%(id)
	comments = dbquery.fetchall(sql)
	return render_template('timeline.html',projects=projects,comments=comments)

@app.route('/approve/<string:id>')
@is_logged_in
def approveID(id):
	sql="UPDATE PROJECTS SET STATUS = 'APPROVED' WHERE PROJECTID = %s"%(id)
	dbquery.inserttodb(sql)
	return redirect(url_for('approve'))



@app.route('/approve')
@is_logged_in

def approve():
		sql="SELECT * FROM PROJECTS WHERE STATUS ='PENDING VERIFICATION'"
		projects=dbquery.fetchall(sql)
		return render_template('approve.html',projects=projects)


#------------------------------logout function----------------------------------
@app.route('/logout')
def logout():
	session.clear()								#Session is destroyed
	flash('You are now logged out','success')
	return redirect(url_for('login'))
#=====================================================


if __name__=='__main__':
	app.secret_key='secret123' #for flash messaging
	app.run(host='0.0.0.0',port =5000,threaded=True) #Debugger is set to 1 for testing and overriding the default port to http port
