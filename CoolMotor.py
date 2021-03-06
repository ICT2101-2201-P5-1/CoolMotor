from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, make_response,session
from mysql import connector
import mysql.connector
import Models.processFile
import Models.editLevel
import Models.gamePlatform
import Models.displayLevel
import Models.dashboard
import telnetCom
from Models.processLogin import LoginForm
import json
import operator


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# For Flash box in Processfile 
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Global Array 
Car_sonic = []
Car_distance = []
Car_speed = []

mapList = []
LevelName = "Default"


# ---------------- APP ROUTES HERE -------------------
@app.route('/', methods=['GET','POST'])
def gamePlatform():
    levelsData = Models.displayLevel.display()

    if request.method == "POST" :  
        get_data = request.form.get('get_data')
        if get_data == '1':
            Sonic, Distance, Speed = telnetCom.receiveData()            
            Car_sonic.append(Sonic)
            Car_distance.append(Distance)
            Car_speed.append(Speed)
        else: 
            # check for lastLevelLoaded, set variable = 1 (tutorial level) if unset
            win = request.get_json().get('win')
            map_id = request.get_json().get('map_id')
            map_difficulty = request.get_json().get('map_difficulty')
            game_min = request.get_json().get('game_minutes')
            game_sec = request.get_json().get('game_seconds')
            dist_travelled = request.get_json().get('dist_travelled')
            # commands = request.get_json().get('commands')

            # car communications
            # print(commands)
            # commandB = bytes(commands[0], 'utf-8')
            # print(commandB)
            # telnetCom.sendCommands(commandB)

            # win game scenario
            if win == 1:

                total_secs = int(game_min) * 60 + int(game_sec)
                # store data to db
                Models.gamePlatform.storeGameDataToDB(map_id, map_difficulty, dist_travelled, total_secs)
                pass
    
    lll = 1

    if request.cookies.get('lastLevelLoaded') is not None:
        lll = request.cookies.get('lastLevelLoaded')

    mapId, mapDifficulty, mapName, mapFile = Models.gamePlatform.readMapDataFromDB(lll)
    commandList, mapData = Models.gamePlatform.initLevelLayout(mapFile)

    return render_template("index.html"
                           , mapLevelLayout=mapData
                           , commandList=commandList
                           , mapName=mapName
                           , mapId=mapId
                           , mapDifficulty=mapDifficulty
                           , levelsData=levelsData
                           , Car_sonic=Car_sonic
                           , Car_distance=Car_distance
                           , Car_speed=Car_speed )


# set last level loaded as cookie..
@app.route('/selectLevel' , methods=['GET','POST'])
def selectLevel():

    res = make_response(redirect(url_for('gamePlatform')))

    if request.method == "POST":
        # check for lastLevelLoaded, set variable = 1 (tutorial level) if unset
        if not request.cookies.get('lastLevelLoaded'):
            res.set_cookie('lastLevelLoaded', '1', max_age=60 * 60 * 24 * 365 * 2)

        else:
            mid = request.form.get('level')
            print(mid)
            res.set_cookie('lastLevelLoaded', mid, max_age=60 * 60 * 24 * 365 * 2)
            
    return res


@app.route('/edit_level', methods=['GET', 'POST'])
def edit_level():
    """
    Edit Level
        Handle receiving of POST request from Map and rendering of CreateLevel page
            @param jsdata The data transfered from drag & drop interface
            @param JSON_obj JSON object in position: "2", value:"goal"
            @param mapList global array
            @return the CreateLevel.html page
    """
    # Get post request from TranserJson(value,data) JS
    if request.method == 'POST':
        jsdata = request.form['javascript_data'] 
        JSON_obj = json.loads(jsdata)  
        # convert JSON string to mapList 
        mapList.append(JSON_obj)
    # sort list 
    mapList.sort(key=operator.itemgetter('position'))
    return render_template("LevelEditor/CreateLevel.html")


@app.route('/getMAPData', methods=['POST'])
def get_MAPData():
    """
        Get Map Data
            Handle receiving of POST request from Level_Editor_Form and rendering of CreateLevel page
                @param CommandList The id list of checked commands
                @param LevelName String levelName user input
                @param Difficulty value 1(easy),2(medium),3(hard)
                @return the CreateLevel.html page
    """
    # Get post request from form when user submit
    if request.method == 'POST':
        CommandList = request.form.getlist('Commands')
        LevelName = request.form.get('LevelName')
        Difficulty = request.form.get('Difficulties')
        status = Models.processFile.writeToMapFile(mapList,LevelName,CommandList, Difficulty)
        # Clear the array after every submission 
        mapList.clear()
        if status == 'success':
            flash("Level created successsfully!")
        else:
            flash("Please select a goal in the map!")
            redirect(url_for('edit_level'))
      
    return render_template("LevelEditor/CreateLevel.html")


@app.route("/displayLevel")
def view_display_Level():
    """
    This routes to the displaylevel.html, that page will display
    all the levels stored in the database and allow for deletes.
    """
    data = Models.displayLevel.display()
    return render_template("LevelEditor/displayLevel.html", title="Level Display", output_data=data)


@app.route("/deletelevel/<int:id>", methods=['POST'])
def delete_level(id):
    """
    This route takes the variable passed by the delete button
    in the displaylevel.html and passes it to the delete function
            @param id           Is the variable that it receives from the displaylevel.html delete button
    """
    Models.displayLevel.delete(id)
    session.pop('_flashes', None)
    flash('Deletion Successful', "info")
    return redirect(url_for('view_display_Level'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    Models.dashboard.getGameDataFromDB()
    return render_template("dashboard.html", data=Models.dashboard.fetchData())


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    form.load()
    # keep output in var change
    status = form.check()
    if status == "Success":
        flash('Login Successful', "info")
        return redirect(url_for('edit_level'))
    elif status == "Fail":
        form.load()
        flash('Wrong Password!')
    elif status == "Timeout":
        form.load()
        flash('Too many incorrect logins incident!')

    return render_template('LevelEditor/login.html', title='Login', form=form)


# -----------------------------Car Communication Testing--------------------------------
@app.route('/command', methods=['GET', 'POST'])
def command():
    if request.method == 'POST':
        command = request.form.get('command')
        print(command)
        commandB = bytes(command, 'utf-8')
        print(commandB)
        telnetCom.sendCommands(commandB)
    return render_template("command.html")


@app.route('/getCarData', methods=['POST'])
def get_data():
    Sonic = telnetCom.receiveData()
    print(Car_data)
    Car_data.append(Sonic)
    return render_template("command.html",Car_data=Car_data )

    
if __name__ == "__main__":
    # Error will be displayed on web page
    app.run(debug=True)

