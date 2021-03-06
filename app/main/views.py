from flask import render_template,g,request
from . import main
from .. import db
from ..models import Student,Score
from sqlalchemy import func
from sqlalchemy import distinct
from . import forms


@main.route("/analyseCourse",methods=["GET","POST"])
def analyseCourse():
    form = forms.NormalForm()
    if form.validate_on_submit():
        courseName=db.session.query(Score.courseName).filter(Score.courseName.like("%"+form.string.data+"%")).first()
        if courseName==None:
            return render_template("analyseCourse.html", studentNum=main.studentNum, form=form,error=True)
        else:
            courseName=courseName.courseName
        terms=db.session.query(distinct(Score.termName)).filter(Score.courseName==courseName).all()
        results=[]
        for i in terms:
            results.append({"termName":i[0],
                            "avg":db.session.query(Score,func.avg(Score.mark).label("avg")).filter(Score.termName==i[0],Score.courseName==courseName).first(),
                            "topStu":db.session.query(Score.mark,Student).filter(Score.studentId==Student.id,
                                        Score.termName==i[0],Score.courseName==courseName).order_by(db.desc(Score.mark)).all()[:10]})
        return render_template('analyseCourse.html', studentNum=main.studentNum,form=form,results=results,courseName=courseName)
    if request.method=="GET":
        return render_template("analyseCourse.html", studentNum=main.studentNum, form=form)


@main.route("/analyseStudent",methods=["GET","POST"])
def analyseStudent():
    form = forms.StudentForm()
    if form.validate_on_submit():
        studentId=form.studentId.data
        terms=db.session.query(Score.termName).filter(Score.studentId == studentId).group_by(Score.termName).all()
        if terms==[]:
            return render_template("analyseStudent.html", studentNum=main.studentNum, form=form,error=True)
        results=[]
        student=db.session.query(Student).filter(Student.id == studentId).first()
        for i in terms:
            results.append({
                "termName":i.termName,"score":db.session.query(Score).filter(Score.studentId==studentId,Score.termName==i.termName).all(),
                            "avg":db.session.query(func.avg(Score.mark)).filter(Score.studentId==studentId,Score.termName==i.termName).scalar()})
        for i in results:
            i["average"]=[]
            avg=db.session.query(Score.studentId,Student.majorName,func.avg(Score.mark).label("avg")).filter(Student.id==Score.studentId,
                                Student.majorName==student.majorName,Score.termName==i["termName"]).group_by(Score.studentId).all()
            i["majorRank"]=len([j for j in avg if j.avg>i["avg"]])+1
            avg=db.session.query(Score.studentId,Student.className,func.avg(Score.mark).label("avg")).filter(Student.id==Score.studentId,
                                Student.className==student.className,Score.termName==i["termName"]).group_by(Score.studentId).all()
            i["classRank"] = len([j for j in avg if j.avg > i["avg"]]) + 1
            for course in i["score"]:
                courseName=course.courseName
                i["average"].append(db.session.query(func.avg(Score.mark).label("avg")).filter(Score.courseName==courseName,Score.termName==i["termName"]).scalar())

        return render_template('analyseStudent.html', studentNum=main.studentNum,form=form,results=results,studentId=studentId)
    if request.method=="GET":
        return render_template("analyseStudent.html", studentNum=main.studentNum,form=form)

@main.route("/analyseClass",methods=["GET","POST"])
def analyseClass():
    form = forms.NormalForm()
    if form.validate_on_submit():
        cls = db.session.query(Student.className,Student.majorName).filter(
            Student.className.like("%" + form.string.data + "%")).first()
        if cls==None:
            return render_template('analyseClass.html', studentNum=main.studentNum, form=form,error=True)

        terms = db.session.query(Score.termName).filter(Score.studentId == Student.id,Student.className==cls.className).group_by(Score.termName).all()
        results = []
        for i in terms:
            results.append({
                "termName": i.termName,
                "classAvg": db.session.query(Score.courseName,func.avg(Score.mark).label("avg")).filter(
                    Score.studentId == Student.id,Score.termName == i.termName,
                    Student.className==cls.className).group_by(Score.courseName).all(),
                "classavg": db.session.query(func.avg(Score.mark)).filter(Score.studentId == Student.id,
                    Student.className==cls.className,Score.termName == i.termName).scalar(),
                "stuNums":db.session.query(func.count(distinct(Student.id))).filter(
                    Score.studentId == Student.id,Student.className==cls.className,
                    Score.termName == i.termName).scalar(),
                "topStu": db.session.query(Student.id,Student.gender,func.avg(Score.mark).label("avg")).filter(
                    Score.studentId == Student.id,Student.className==cls.className,
                    Score.termName == i.termName).group_by(Student.id).order_by(db.desc("avg")).all()[:5],
                "lowStu": db.session.query(Student.id,Student.gender,func.avg(Score.mark).label("avg")).filter(
                    Score.studentId == Student.id, Score.termName==i.termName,Student.className == cls.className).group_by(Student.id).order_by(
                    "avg").all()[:5]
            }
            )
        for i in results:
            i["average"] = []
            avg = db.session.query(Student.className, func.avg(Score.mark).label("avg")).filter(
                Student.id == Score.studentId,
                Student.majorName == cls.majorName, Score.termName == i["termName"]).group_by(Student.className).all()
            i["majorRank"] = len([j for j in avg if j.avg > i["classavg"]]) + 1
            for course in i["classAvg"]:
                i["average"].append(
                    db.session.query(func.avg(Score.mark).label("avg")).filter(Score.courseName == course.courseName,
                                                                               Score.termName == i["termName"]
                                                                               ).scalar())
        return render_template('analyseClass.html', studentNum=main.studentNum,form=form,results=results,cls=cls)
    if request.method=="GET":
        return render_template("analyseClass.html", studentNum=main.studentNum,form=form)

@main.before_app_first_request
def bf_first_request():
    main.studentNum = db.session.query(func.count(Student.id)).scalar()

@main.route("/student",methods=["GET","POST"])
def student():
    form = forms.StudentForm()
    if form.validate_on_submit():
        studentId=form.studentId.data
        student=db.session.query(Student).filter(Student.id == studentId).first()
        if student==None:
            return render_template('students.html', studentNum=main.studentNum, form=form, error=True)
        courses=db.session.query(Score).filter(Score.studentId==studentId).order_by(db.desc(Score.mark)).all()
        return render_template('students.html', studentNum=main.studentNum,form=form,student=student,courses=courses)
    if request.method=="GET":
        return render_template("students.html", studentNum=main.studentNum,form=form)

@main.route("/course",methods=["GET","POST"])
def course():
    form = forms.CourseForm()
    if form.validate_on_submit():
        courseName = db.session.query(Score.courseName).filter(
            Score.courseName.like("%" + form.courseName.data + "%")).first()
        if courseName == None:
            return render_template("courses.html", studentNum=main.studentNum, form=form, error=True)
        else:
            courseName = courseName.courseName
        courses = db.session.query(Score.courseName,Score.courseId,func.count(Score.studentId).label("nums"),
                                   Score.credit,Score.termName,Score.courseDe,func.avg(Score.mark).label('avg')).filter(Score.courseName.like("%"+courseName+"%"))\
                                .group_by(Score.termName,Score.courseName).all()
        names=[]
        if courses:
            for i in courses:
                names.append(i.courseName)
                students=db.session.query(Score).filter(Score.courseName.in_(names)).order_by(db.desc(Score.mark)).all()[:20]
        else:
            students=[]
        return render_template('courses.html', studentNum=main.studentNum, form=form, courses=courses,students=students,courseName=courseName)
    if request.method == "GET":
        return render_template("courses.html", studentNum=main.studentNum, form=form)

@main.route("/courseRank",methods=["GET","POST"])
def courseRank():
    topcourse=db.session.query(Score.courseName,func.count(Score.studentId).label("nums"),Score.classId,
                     Score.credit, Score.termName, Score.courseDe, func.avg(Score.mark).label('avg')).group_by(Score.termName,
                                    Score.courseName,Score.classId).order_by(db.desc("avg")).all()[:100]
    return render_template("courseRank.html", studentNum = main.studentNum, courses=topcourse)

@main.route("/specializedRank",methods=["GET","POST"])
def specializedRank():
    software_score = Student.query.filter_by(majorName = '软件工程').order_by(Student.average.desc()).all()[:20]
    civil_score = Student.query.filter_by(majorName = '土木工程').order_by(Student.average.desc()).all()[:20]
    info_score = Student.query.filter_by(majorName = '信息管理与信息系统').order_by(Student.average.desc()).all()[:20]
    e_bussiness_score = Student.query.filter_by(majorName = '电子商务').order_by(Student.average.desc()).all()[:20]
    e_bussiness_s_score = Student.query.filter_by(majorName = '电子商务（专）').order_by(Student.average.desc()).all()[:20]
    net_score = Student.query.filter_by(majorName = '网络工程').order_by(Student.average.desc()).all()[:17]
    cs_score = Student.query.filter_by(majorName = '计算机科学与技术').order_by(Student.average.desc()).all()[:20]
    specializedScore = []
    specializedScore.append({'name': '软件工程', 'score': software_score})
    specializedScore.append({'name': '土木工程', 'score': civil_score})
    specializedScore.append({'name': '信息管理与信息系统', 'score': info_score})
    specializedScore.append({'name': '电子商务', 'score': e_bussiness_score})
    specializedScore.append({'name': '电子商务（专）', 'score': e_bussiness_s_score})
    specializedScore.append({'name': '网络工程', 'score': net_score})
    specializedScore.append({'name': '计算机科学与技术', 'score': cs_score})
    g.specializedScore = specializedScore
    return render_template("specializedRank.html", studentNum = main.studentNum, g = g)

@main.route("/majorRank",methods=["GET","POST"])
def majorRank():
    form = forms.NormalForm()
    if form.validate_on_submit():
        majorName = form.string.data
        result=db.session.query(Student).filter(Student.majorName.like("%"+majorName+"%")).order_by(db.desc(Student.average)).all()[:50]
        if result==[]:
            error=True
        else:
            error=False
        return render_template('majorRank.html', studentNum=main.studentNum, form=form, result=result,error=error)
    if request.method == "GET":
        return render_template("majorRank.html", studentNum=main.studentNum, form=form)

@main.route("/totalRank",methods=["GET","POST"])
def totalRank():
    form = forms.StudentForm()
    if form.validate_on_submit():
        studentId = form.studentId.data
        student = db.session.query(Student).filter(Student.id == studentId).first()
        if student==None:
            return render_template("yourRank.html", studentNum=main.studentNum, form=form,error=True)
        student.avgMajor=db.session.query(Student).filter(Student.average > student.average,Student.majorName==student.majorName).all()
        student.gpaMajor=db.session.query(Student).filter(Student.jidian > student.jidian,Student.majorName==student.majorName).all()
        student.avgMajorRank = len(student.avgMajor) + 1
        student.gpaMajorRank = len(student.gpaMajor) + 1
        student.avgClass= db.session.query(Student).filter(Student.average > student.average,
                                                            Student.className == student.className).all()
        student.gpaClass = db.session.query(Student).filter(Student.jidian > student.jidian,
                                                            Student.className == student.className).all()
        student.avgClassRank = len(student.avgClass) + 1
        student.gpaClassRank = len(student.gpaClass) + 1
        return render_template('yourRank.html', studentNum=main.studentNum, form=form, student=student)
    if request.method == "GET":
        return render_template("yourRank.html", studentNum=main.studentNum, form=form)

@main.route("/")
def index():
    g.studentNum=main.studentNum
    major=db.session.query(Student.majorName,func.count(Student.id).label("majorNum")).group_by(Student.majorName).all()
    g.majorNum=len(major)
    totalNum = 0
    # 计算各专业占百分比
    majors = []
    for classes in major:
        totalNum += classes.majorNum
        majors.append(list(classes))

    for classes in majors:
        classes[1] = (int(classes[1] / totalNum * 100))

    top20score = Student.query.order_by(Student.average.desc()).all()[:20]
    g.major = major
    g.majors=majors
    g.score = top20score
    course=db.session.query(Score.courseName,func.count(Score.id).label("courseNum")).group_by(Score.courseName).all()
    g.courseNum=len(course)
    g.course=course
    male = db.session.query(Student.id).filter_by(gender='男').count()
    female = db.session.query(Student.id).filter_by(gender='女').count()
    g.male = male
    g.female = female
    return render_template("index.html",studentNum=main.studentNum,g=g)

@main.route("/analyseMajor",methods=["GET","POST"])
def analyseMajor():
    form = forms.NormalForm()
    if form.validate_on_submit():
        majorName = db.session.query(Student.majorName).filter(
            Student.majorName.like("%" + form.string.data + "%")).first()
        if majorName==None:
            return render_template("analyseMajor.html", studentNum=main.studentNum, form=form,error=True)
        else:
            majorName=majorName.majorName
        terms=db.session.query(Score.termName).filter(Student.id==Score.studentId,Student.majorName==majorName).group_by(Score.termName).all()
        results=[]
        for i in terms:
            results.append({
                "termName": i.termName,
                "majoravg":db.session.query(func.avg(Score.mark)).filter(
                    Score.studentId == Student.id,Score.termName == i.termName, Student.majorName == majorName).scalar(),
                "majorAvg": db.session.query(Score.courseName,Score.courseDe,Score.credit, func.avg(Score.mark).label("avg")).filter(
                    Score.studentId == Student.id,Score.termName == i.termName, Student.majorName == majorName).group_by(Score.courseName).all(),
                "class": db.session.query(Student.className,func.avg(Score.mark).label("avg")).filter(Score.studentId == Student.id,
                    Student.majorName==majorName,Score.termName == i.termName).group_by(Student.className).all(),
                "topStu":db.session.query(Student.id,Student.gender,Student.className,func.avg(Score.mark).label("avg")).filter(Score.studentId == Student.id,
                           Student.majorName==majorName,Score.termName == i.termName).group_by(Student.id).order_by(db.desc("avg")).all()[:20]})
        return render_template('analyseMajor.html', studentNum=main.studentNum,form=form,results=results,majorName=majorName)
    if request.method=="GET":
        return render_template("analyseMajor.html", studentNum=main.studentNum,form=form)

@main.route("/score",methods=["GET","POST"])
def score():
    form=forms.Score()
    if request.method=="POST":
        maps = {"major": "专业", "student": "学号", "department": "学院",
                "grade": "年级",
                "class": '班级', "gender": "性别", "course": "课程名称",
                "courseDe": "课程性质"}
        g.info=form.info.data
        g.search=form.search.data
        (g.n,g.avg, g.results, g.youxiu, g.bujige,g.nums,g.youxiulv,g.bujigelv,g.others)=scoreAnalysis(g.info,g.search)
        if g.n==0:
            return render_template("scores.html", studentNum=main.studentNum,form=form,error=True)
        g.info=maps[g.info]
        return render_template("scores.html", studentNum=main.studentNum, form=form,g=g)
    if request.method=="GET":
        return render_template("scores.html", studentNum=main.studentNum,form=form)

@main.route("/compareStudent",methods=["GET","POST"])
def compareStudent():
    form = forms.CompareForm()
    if form.validate_on_submit():
        studentId1 = form.Name1.data
        studentId2 = form.Name2.data
        student1 = db.session.query(Student).filter(Student.id == studentId1).first()
        student2 = db.session.query(Student).filter(Student.id == studentId2).first()
        if not (student1 and student2):
            return render_template("compareStudent.html", studentNum=main.studentNum, form=form,error=True)
        if student1:
            student1.courseNums = db.session.query(func.count("*")).filter(Score.studentId == studentId1).scalar()
            student1.courses = db.session.query(Score).filter(Score.studentId == studentId1).all()
            student1.youxiuNums=db.session.query(func.count("*")).filter(Score.studentId == studentId1,Score.mark>=90).scalar()
            student1.bujigeNums=db.session.query(func.count("*")).filter(Score.studentId== studentId1,Score.mark<60).scalar()
            student1.youxiuCourses = db.session.query(Score).filter(Score.studentId == studentId1).order_by(
                db.desc(Score.mark)).all()[:5]
        if student2:
            student2.courseNums = db.session.query(func.count("*")).filter(Score.studentId == studentId2).scalar()
            student2.courses = db.session.query(Score).filter(Score.studentId == studentId2).all()
            student2.youxiuNums=db.session.query(func.count("*")).filter(Score.studentId == studentId2,Score.mark>=90).scalar()
            student2.bujigeNums=db.session.query(func.count("*")).filter(Score.studentId== studentId2,Score.mark<60).scalar()
            student2.youxiuCourses = db.session.query(Score).filter(Score.studentId == studentId2).order_by(db.desc(Score.mark)).all()[:5]
        return render_template("compareStudent.html", studentNum = main.studentNum, form=form,student=[student1,student2])
    if request.method == "GET":
        return render_template("compareStudent.html", studentNum=main.studentNum, form=form)

@main.route("/compareCourse",methods=["GET","POST"])
def compareCourse():
    form=forms.CompareForm()
    if request.method=="POST":
        courseName1 = form.Name1.data
        courseName2 = form.Name2.data
        courses1 = db.session.query(Score).filter(
            Score.courseName.like("%"+courseName1+"%")).group_by(Score.termName, Score.classId).all()
        courses2 = db.session.query(Score).filter(
            Score.courseName.like("%"+courseName2+"%")).group_by(Score.termName, Score.classId).all()
        if courses1==courses2==[]:
            return render_template("compareCourse.html", studentNum=main.studentNum, form=form, error=True)
        if courses1:
            for i in courses1:
                i.studentNums = db.session.query(func.count("*")).filter(Score.courseName == i.courseName,
                                                                         Score.termName == i.termName,
                                                                         Score.classId == i.classId).scalar()
                i.avg = db.session.query(func.avg(Score.mark)).filter(Score.courseName == i.courseName,
                                                                  Score.termName == i.termName,
                                                                  Score.classId == i.classId).scalar()
                i.youxiuStudents = db.session.query(Score).filter(Score.courseName == i.courseName,
                                                              Score.termName == i.termName, Score.classId == i.classId).order_by(db.desc(Score.mark)).all()[:5]
        if courses2:
            for i in courses2:
                i.studentNums = db.session.query(func.count("*")).filter(Score.courseName == i.courseName,
                                                                         Score.termName == i.termName,
                                                                         Score.classId == i.classId).scalar()
                i.avg = db.session.query(func.avg(Score.mark)).filter(Score.courseName == i.courseName,
                                                                  Score.termName == i.termName,
                                                                  Score.classId == i.classId).scalar()
                i.youxiuStudents = db.session.query(Score).filter(Score.courseName == i.courseName,
                                                              Score.termName == i.termName, Score.classId == i.classId).order_by(db.desc(Score.mark)).all()[:5]
        return render_template("compareCourse.html", studentNum=main.studentNum, form=form, courses=[courses1, courses2])
    return render_template("compareCourse.html", studentNum=main.studentNum, form=form)

def scoreAnalysis(key,value):
    maps = {"major": Student.majorName, "student": Student.id,"department": Student.departmentName, "grade": Student.grade,
            "class": Student.className, "gender": Student.gender,"course":Score.courseName,"courseDe":Score.courseDe}
    args=db.session.query(maps[key].label("arg")).filter(maps[key].like("%"+value+"%")).group_by(maps[key]).all()
    if len(args)==0:
        return (0, None, None, None, None, None, None, None, None)
    if len(args)==1:
        avg=db.session.query(func.avg(Score.mark)).filter(maps[key].like("%"+value+"%"),Student.id==Score.studentId).scalar()
        results=db.session.query(Score.studentId,Score,Score.courseName,Score.credit,Score.termName,Score.courseDe,
                                 Score.mark).filter(maps[key].like("%"+value+"%"),Student.id==Score.studentId).order_by(db.desc(Score.mark)).all()
        youxiu=db.session.query(func.count("*")).filter(maps[key].like("%"+value+"%"),Student.id==Score.studentId,Score.mark>=90).scalar()
        bujige=db.session.query(func.count("*")).filter(maps[key].like("%"+value+"%"),Student.id==Score.studentId,Score.mark<60).scalar()
        nums = len(results)
        if results==[]:
            youxiulv=bujigelv=0
        else:
            youxiulv = youxiu / len(results)
            bujigelv = bujige / len(results)
        result = [{"name":args[0].arg,"avg":avg,"results":results,"youxiu":youxiu,"bujige":bujige,"youxiulv":youxiulv,"bujigelv":bujigelv,"num":len(results)}]
        return (1,avg,results,youxiu,bujige,nums,youxiu,bujige,result)
    else:
        zongarg = db.session.query(func.avg(Score.mark)).filter(maps[key].like("%" + value + "%"),
                                                                Student.id == Score.studentId).scalar()
        zongresults = db.session.query(Score.studentId,Score,Score.courseName,Score.credit,Score.termName,Score.courseDe,
                                 Score.mark).filter(maps[key].like("%" + value + "%"),
                                                                       Student.id == Score.studentId).order_by(db.desc(Score.mark)).all()
        zongyouxiu = db.session.query(func.count("*")).filter(maps[key].like("%" + value + "%"),
                                                          Student.id == Score.studentId, Score.mark >= 90).scalar()
        zongbujige = db.session.query(func.count("*")).filter(maps[key].like("%" + value + "%"),
                                                          Student.id == Score.studentId, Score.mark < 60).scalar()
        zongnums=len(zongresults)
        if zongresults==[]:
            zongyouxiulv=zongbujigelv=0
        else:
            zongyouxiulv = zongyouxiu / len(zongresults)
            zongbujigelv = zongbujige / len(zongresults)
        results=[]
        for i in args:
            results.append({"name":i.arg,
                "avg":db.session.query(func.avg(Score.mark)).filter(maps[key]==i.arg,
                                                          Student.id == Score.studentId).scalar(),
            "results":db.session.query(Score.studentId, Score.mark).filter(maps[key]==i.arg,
                                                                       Student.id == Score.studentId).order_by(db.desc(Score.mark)).all(),
            "youxiu":db.session.query(func.count("*")).filter(maps[key]==i.arg,
                                                          Student.id == Score.studentId, Score.mark >= 90).scalar(),
            "bujige": db.session.query(func.count("*")).filter(maps[key]==i.arg,
                                                                          Student.id == Score.studentId,
                                                                          Score.mark < 60).scalar()})
        for i in results:
            if i["results"] == []:
                i["youxiulv"] = i["bujigelv"] = 0
            else:
                i["youxiulv"]=i["youxiu"]/len(i["results"])
                i["bujigelv"]=i["bujige"]/len(i["results"])
            i["num"]=len(i["results"])
        return (len(args),zongarg,zongresults,zongyouxiu,zongbujige,zongnums,zongyouxiulv,zongbujigelv,results)
