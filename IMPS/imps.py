########################################################################
### IMPORT LIBRARIES
########################################################################
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    make_response,
    request,
    # login
)
import bcrypt

import os
import sys
import shutil
import pathlib

import configparser
import toml

from array import array

import qrcode
from PIL import Image, ImageOps

from flask_paginate import Pagination, get_page_parameter

import mysql.connector as sql_db
from mysql.connector import errorcode

import gzip

import datetime
import time
from datetime import date

import re
import requests

from werkzeug.utils import secure_filename

from functools import wraps

app = Flask(__name__)

global saved_search

########################################################################
### IMPORT CONFIGURATION FROM TOML FILE
########################################################################

### TEST THAT THE CONFIGURATION FILE CAN BE OPENED
try:
    with open("imps_config.toml", mode="r") as f:
        imps_config = toml.load(f)
except:
    os.system("clear")
    print(
        "IMPS CONFIGURATION ERROR -- IMPS cannot open the \
             imps_config.toml file which is required. Check that"
    )
    print(
        "this file is in the same directory as imps.py and \
             has the correct ownership and permissions."
    )
    sys.exit()

### IMPORT CONFIGURATION
global dbhost
dbhost = imps_config["database"]["host"]
global dbname
dbname = imps_config["database"]["name"]
global dbuser
dbuser = imps_config["database"]["user"]
global dbpass
dbpass = imps_config["database"]["password"]

global IMPS_PATH
IMPS_PATH = imps_config["directories"]["imps_path"]
global BACKUP_DIR
BACKUP_DIR = imps_config["directories"]["backup_dir"]
global ITEM_IMAGE_DIR
ITEM_IMAGE_DIR = imps_config["directories"]["item_image_dir"]
global IMPS_IP
IMPS_IP = imps_config["directories"]["imps_ip"]

global HASHED_IMPS_PASS
## GET PASSWORD AND HASH
pass_to_hash = imps_config["password"]["password"]
bytes = pass_to_hash.encode("utf-8")
salt = bcrypt.gensalt()
HASHED_IMPS_PASS = bcrypt.hashpw(bytes, salt)

########################################################################
### CONFIGURE SQL CONNECTION
########################################################################
try:
    mydb = sql_db.connect(host=dbhost, database=dbname, user=dbuser, password=dbpass)
    mydb.ping(True)
    mydb.autocommit = True
except:
    print("no db")


########################################################################
### CONFIGURE UPLOADS
########################################################################

UPLOAD_FOLDER = ITEM_IMAGE_DIR
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = "/" + ITEM_IMAGE_DIR


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_users(offset=0, per_page=10):
    return users[offset : offset + per_page]


########################################################################
### USER MANAGEMENT
########################################################################


###############################################################
### CUSTOM DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        saved_pass = request.cookies.get("loggedin")
        if not saved_pass:
            return redirect("/login")
        if HASHED_IMPS_PASS != saved_pass.encode("utf-8"):
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


#################################################
###LOGIN PAGE
@app.route("/login")
def login():

    ### SHOW THE LOGIN PAGE
    response = make_response(
        render_template(
            "usr_login.html",
            logged_in=False,
        )
    )
    return response


@app.route("/attemptlogin", methods=["POST"])
def attemptlogin():
    HASHED_IMPS_PASS
    userPassword = request.form["password"]

    ## MATCH AGAINST PASS SET IN imps_config.toml
    userBytes = userPassword.encode("utf-8")
    pass_match = bcrypt.checkpw(userBytes, HASHED_IMPS_PASS)

    if pass_match == True:
        response = make_response(render_template("index.html"))
        response.set_cookie("loggedin", HASHED_IMPS_PASS, max_age=36000)
        return response

    else:
        return render_template(
            "usr_loginfailed.html",
            logged_in=False,
        )


#################################################
###LOGOUT PAGE
@app.route("/logout")
def logout():

    ### SHOW THE LOGGED OUT PAGE
    response = make_response(
        render_template(
            "usr_logout.html",
            logged_in=False,
        )
    )
    response.delete_cookie("loggedin")
    return response


#################################################
###LOGIN FAILED
@app.route("/loginfailed")
def loginfailed():
    response = make_response(
        render_template(
            "usr_loginfailed.html",
            logged_in=False,
        )
    )
    return response


########################################################################
### WELCOME PAGE
########################################################################
@app.route("/welcome")
def welcome():

    ########################################
    ### TEST DATABSE

    ### TEST CONNECTION
    try:
        cursor = mydb.cursor(prepared=True)
        cursor.close()
        db_conn = True
    except:
        db_conn = False

    ### TEST DB BOX TABLE EXISTS
    test_query = """SELECT * FROM boxes WHERE box_num = 1"""
    try:
        cursor = mydb.cursor()
        cursor.execute(test_query)
        result = cursor.fetchone()
        query_success = cursor.rowcount
        cursor.close()
        if query_success >= 1:
            db_tables = True
    except:
        db_tables = False

    ########################################
    ### TEST PATHS

    ### IMPS PATH
    if os.path.exists(IMPS_PATH):
        imps_path_config = True
    else:
        imps_path_config = False

    ### ITEM IMAGE PATH
    if os.path.exists(IMPS_PATH + ITEM_IMAGE_DIR):
        item_image_config = True
    else:
        item_image_config = False

    ### BACKUP PATH
    if os.path.exists(BACKUP_DIR):
        backup_config = True
    else:
        backup_config = False

    ### SHOW WELCOME PAGE
    return render_template(
        "firstrun.html",
        db_conn=db_conn,
        db_tables=db_tables,
        imps_path_config=imps_path_config,
        item_image_config=item_image_config,
        backup_config=backup_config,
    )


########################################################################
### DELETE first.run
########################################################################
@app.route("/del_firstrun")
def del_firstrun():
    first_run = IMPS_PATH + "/first.run"
    not_first_run = IMPS_PATH + "/not_first_run"
    try:
        os.rename(first_run, not_first_run)
    except:
        print("File first.run already deleted")

    response = make_response(render_template("index.html", cookies=request.cookies))


########################################################################
### HOME PAGE
########################################################################
@app.route("/")
@login_required
def home():
    ####################################################################
    ### IF THIS IS THE INITAL RUN OF IMPS, TEST SETTINGS
    if os.path.isfile("first.run"):
        return redirect(url_for("welcome"))

    ####################################################################
    ### OTHERWISE SHOW THE HOME PAGE
    else:
        response = make_response(render_template("index.html", cookies=request.cookies))
        return response


########################################################################
### SEARCH
########################################################################


#################################################
### SEARCH TERM INPUT
@app.route("/search")
@login_required
def search():
    ### SHOW THE SEARCH PAGE
    return render_template("search.html")


#################################################
### PERFORM SEARCH AND SHOW RESULTS
@app.route("/search_result/<query_term>")
@login_required
def search_result(query_term):
    #####################################
    ############# PAGINATION
    limit = 35
    page_req = request.args.get("page")
    if page_req == None:
        offset = 0
    else:
        offset = limit * (int(page_req) - 1)
    ########################################################################

    ### SET UP SEARCH QUERY : SEARCH BOTH ITEM NAMES AND DESCRIPTIONS
    item_query = """ SELECT * FROM items WHERE item_name LIKE \
                     CONCAT('%',?,'%') OR item_desc LIKE \
                     CONCAT('%',?,'%') OR item_cat LIKE \
                     CONCAT('%',?,'%') ORDER BY item_num DESC """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="""Database error when accessing inventory. \
                 Could not connect.""",
            err_page_from="/",
        )
    cursor.execute(item_query, (query_term, query_term, query_term))
    result = cursor.fetchall()
    item_list = result
    cursor.close()
    item_list.sort()

    ### GET NUMBER OF RESULTS
    num_item_query = """ SELECT COUNT(*) FROM items WHERE item_name LIKE \
                         CONCAT('%',?,'%') OR item_desc LIKE \
                         CONCAT('%',?,'%') """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(num_item_query, (query_term, query_term))
    result = cursor.fetchone()
    cursor.close()
    total = result[0]

    #####################################
    ############# PAGINATION
    last_item = offset + limit
    item_list = item_list[offset : (offset + limit)]
    search = False

    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        page=page,
        total=total,
        search=search,
        per_page=35,
    )

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### READ COOKIE AND SHOW APPROPRIATE VIEW
    current_view = request.cookies.get("view")
    if current_view == "mobile":
        response = make_response(
            render_template(
                "search_result_mobile.html",
                item_list=item_list,
                page=page,
                pagination=pagination,
                cookies=request.cookies,
                search_term=query_term,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            )
        )
        return response
    else:
        response = make_response(
            render_template(
                "search_result.html",
                item_list=item_list,
                page=page,
                pagination=pagination,
                cookies=request.cookies,
                search_term=query_term,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
                info_column=info_column,
                photo_column=photo_column,
                date_column=date_column,
                cat_column=cat_column,
                box_column=box_column,
            )
        )
        return response


########################################################################
### SHOW ALL ITEMS / INVENTORY
########################################################################
@app.route("/inventory")
@login_required
def inventory():
    #####################################
    ############# PAGINATION
    limit = 35
    page_req = request.args.get("page")
    if page_req == None:
        offset = 0
    else:
        offset = limit * (int(page_req) - 1)

    ### CHECK CONNECTION, ATTEMPT TO RECONNECT IF NONE
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="""Database error when accessing inventory. \
                    Could not connect.""",
            err_page_from="/",
        )
    ### GET NUMBER OF ITEMS FROM DB
    num_query = " SELECT COUNT(*) FROM items  "
    cursor = mydb.cursor(prepared=True)
    cursor.execute(num_query)
    result = cursor.fetchone()
    cursor.close()
    total = result[0]

    ### INVENTORY
    ### SET UP ALL ITEMS QUERY
    inv_query = """ SELECT * FROM items ORDER BY item_num DESC \
                    LIMIT ? OFFSET ? """

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(inv_query, (limit, offset))
    result = cursor.fetchall()
    cursor.close()
    item_list = result

    ### DETERMINE IF FROM SEARCH PAGE
    search = False
    q = request.args.get("q")
    if q:
        search = True

    #####################################
    ############# PAGINATION
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        page=page,
        total=total,
        search=search,
        per_page=35,
    )
    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### GET COOKIE AND SHOW THE APPROPRAITE VIEW
    current_view = request.cookies.get("view")
    if current_view == "mobile":
        return render_template(
            "inventory_mobile.html",
            page=page,
            item_list=result,
            pagination=pagination,
            ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        )
    else:
        return render_template(
            "inventory.html",
            item_list=item_list,
            page=page,
            pagination=pagination,
            ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            info_column=info_column,
            photo_column=photo_column,
            date_column=date_column,
            cat_column=cat_column,
            box_column=box_column,
        )


########################################################################
### BOX INTERACTIONS
########################################################################


#################################################
### LIST OF ALL BOXES
@app.route("/boxlist")
@login_required
def boxlist():

    ### QUERY FOR ALL BOXES
    allbox_query = "SELECT * FROM boxes ORDER BY box_num;"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="""Database error when accessing box list. \
                           Could not connect.""",
            err_page_from="/",
        )
    cursor.execute(allbox_query)
    result = cursor.fetchall()
    categories = result
    box_list = result

    ### QUERY FOR BOX NUMBERS OF BOXES THAT ARE NOT EMPTY
    not_empty_box_query = """SELECT box_num FROM items WHERE item_num >0 \
                             ORDER BY box_num;"""
    cursor = mydb.cursor()
    cursor.execute(not_empty_box_query)
    result = cursor.fetchall()
    not_empty_list = result
    cursor.close()

    ### CREATE A LIST OF IN-USE BOX NUMBERS
    not_empty_box_num_list = []
    for i in not_empty_list:
        not_empty_box_num_list.append(i[0])

    ### ELIMINATE DUPLICATES
    not_empty_box_num_list = list(set(not_empty_box_num_list))

    ### SHOW THE LIST OF BOXES PAGE
    return render_template(
        "boxes/boxlist.html",
        box_list=box_list,
        not_empty_box_num_list=not_empty_box_num_list,
    )


#################################################
### LIST BOXES BY LOCATION
@app.route("/boxlistbyloc/<boxlocation>")
@login_required
def boxlistbyloc(boxlocation):

    box_loc = boxlocation
    ### QUERY FOR ALL BOXES
    boxloc_query = """SELECT * FROM boxes WHERE box_loc = ? ;"""
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box list. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(boxloc_query, (box_loc,))
    result = cursor.fetchall()
    cursor.close()
    box_list = result

    ### QUERY FOR BOX NUMBERS OF BOXES THAT ARE NOT EMPTY
    not_empty_box_query = "SELECT box_num FROM items ORDER BY box_num;"
    cursor = mydb.cursor()
    cursor.execute(not_empty_box_query)
    result = cursor.fetchall()
    not_empty_list = result
    cursor.close()

    ### CREATE A LIST OF IN-USE BOX NUMBERS
    not_empty_box_num_list = []
    for i in not_empty_list:
        not_empty_box_num_list.append(i[0])

    ### ELIMINATE DUPLICATES
    not_empty_box_num_list = list(set(not_empty_box_num_list))

    ### SHOW THE LIST OF BOXES PAGE
    return render_template(
        "boxes/boxlist.html",
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        not_empty_box_num_list=not_empty_box_num_list,
        box_list=box_list,
        show_location=boxlocation,
    )


#################################################
### SELECT BOX TO VIEW BY NUMBER
@app.route("/bybox")
@login_required
def bybox():

    ITEM_IMAGE_DIR
    ### QUERY EXISTING BOX NUMBERS
    available_box_nums_query = "SELECT boxes.box_num FROM boxes;"
    try:
        cursor = mydb.cursor()
        cursor.execute(available_box_nums_query)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box list. Could not connect.",
            err_page_from="/",
        )

    result = cursor.fetchall()
    num_items = len(result)
    available_boxes = []
    cursor.close()

    ### TURN RESULT INTO A LIST
    for i in range(num_items):
        container = list(result[i])
        available_boxes.insert(1, container.pop())

    ### SHOW BOX SELECTION PAGE
    return render_template(
        "items/bybox.html",
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        available_boxes=available_boxes,
    )


#################################################
### SELECT CATEGORY TO VIEW
@app.route("/bycategory")
@login_required
def bycategory():

    ITEM_IMAGE_DIR
    ### QUERY FOR ALL CATEGORIES IN CAT TABLE
    all_cats_query = "SELECT cat_name FROM categories;"
    try:
        cursor = mydb.cursor()
        cursor.execute(all_cats_query)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing categories. Could not connect.",
            err_page_from="/",
        )

    result = cursor.fetchall()
    cursor.close()

    ### TURN RESULT INTO A LIST
    num_cats = len(result)
    all_cats = []
    for i in range(num_cats):
        container = list(result[i])
        all_cats.insert(1, container.pop())

    ### QUERY DB FOR ALL CATEGORIES ASSIGNED TO ITEMS
    used_cats_query = "SELECT item_cat FROM items;"
    cursor = mydb.cursor()
    cursor.execute(used_cats_query)
    result = cursor.fetchall()
    cursor.close()

    ### TURN RESULT INTO A LIST
    num_cats = len(result)
    used_cats = []
    for i in range(num_cats):
        container = list(result[i])
        used_cats.insert(1, container.pop())

    ### CREATE A LIST OF ONLY THOSE CATS WHICH CONTAIN ITEMS
    available_cats = list(set(all_cats).intersection(used_cats))
    ### SORT THE LIST
    available_cats = sorted(available_cats)

    ### SHOW CATEGORY SELECTION PAGE
    return render_template(
        "items/bycategory.html",
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        available_cats=available_cats,
    )


#################################################
### SELECT LOCATION TO VIEW
@app.route("/byloc/")
@login_required
def byloc():

    ITEM_IMAGE_DIR

    ### QUERY BOXES TO DETERMINE LOCATIONS IN USE
    used_locs_query = "SELECT box_loc FROM boxes;"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="""Database error when accessing locations. \
                          Could not connect.""",
            err_page_from="/",
        )
    cursor.execute(used_locs_query)
    result = cursor.fetchall()
    num_locs = len(result)
    used_locs = []
    cursor.close()

    ### TURN RESULT INTO A LIST
    for i in range(num_locs):
        container = list(result[i])
        used_locs.insert(1, container.pop())

    ### ELIMINATE DUPES AND SORT LIST
    used_locs = list(set(used_locs))
    available_locs = sorted(used_locs)

    ### SHOW LOCATION SELECTION PAGE
    return render_template(
        "boxes/bylocation.html",
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        available_locs=available_locs,
    )


#################################################
### SWITCH BOX VIEW
@app.route("/boxviewswitch/<box_num>")
@login_required
def box_view_switch(box_num):

    ITEM_IMAGE_DIR

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### BOX CONTENT QUERY
    query_box = box_num
    query_statement = """ SELECT * FROM items WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
        cursor.execute(query_statement, (query_box,))
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box content. Could not connect.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    item_list = result

    ### BOX NAME QUERY
    box_name_query = """ SELECT box_name FROM boxes WHERE box_num = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(box_name_query, (query_box,))
    result = cursor.fetchone()
    box_name = result[0]

    cursor.close()

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### FLIP THE VIEW COOKIE AND RETURN APPROPRIATE VIEW
    current_view = request.cookies.get("view")

    ### SHOW THE BOX CONTENT BASED ON VIEW
    if current_view == "mobile":
        response = make_response(
            render_template(
                "items/itemsinbox.html",
                item_list=item_list,
                box_name=box_name,
                box_num=box_num,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
                info_column=info_column,
                photo_column=photo_column,
                date_column=date_column,
                cat_column=cat_column,
                box_column=box_column,
            )
        )
        response.set_cookie("view", "desk")
        return response
    else:
        response = make_response(
            render_template(
                "items/itemsinbox_mobile.html",
                item_list=item_list,
                box_name=box_name,
                box_num=box_num,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            )
        )
        response.set_cookie("view", "mobile")
        return response


#################################################
### DISPLAY BOX CONTENTS OF SELECTED BOX
@app.route("/boxshowcontent/<box_num>", methods=["POST", "GET"])
@login_required
def showbox(box_num):

    ITEM_IMAGE_DIR

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Invalid page access. Box number must be an int.",
            err_page_from="/",
        )

    ### BOX CONTENT QUERY
    query_box = box_num
    items_in_box_query = """ SELECT * FROM items WHERE box_num = ?  """
    try:
        cursor = mydb.cursor(prepared=True)
        cursor.execute(items_in_box_query, (query_box,))
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box contents. Could not connect.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    cursor.close()
    ### EMPTY BOX VIEW IF THE SELECTED BOX HAS NO ITEMS
    if not result:
        return render_template(
            "errorpage.html",
            err_message="The selected box does not contain any items or the box does not exist.",
            err_page_from="/bybox",
        )
    item_list = result
    ### BOX NAME QUERY
    box_name_query = """ SELECT box_name FROM boxes WHERE box_num = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(box_name_query, (query_box,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access boxes.",
            err_page_from="/",
        )
    box_name = result[0]
    cursor.close()

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### SHOW THE BOX CONTENT PAGE BASED ON VIEW
    current_view = request.cookies.get("view")
    if current_view == "mobile":
        response = make_response(
            render_template(
                "items/itemsinbox_mobile.html",
                item_list=item_list,
                box_name=box_name,
                box_num=box_num,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            )
        )
        return response

    else:
        box_name = box_name
        response = make_response(
            render_template(
                "items/itemsinbox.html",
                item_list=item_list,
                box_name=box_name,
                box_num=box_num,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
                info_column=info_column,
                photo_column=photo_column,
                date_column=date_column,
                cat_column=cat_column,
                box_column=box_column,
            )
        )
        return response


#################################################
### CREATE AND SHOW BOX LABEL / QR CODE
@app.route("/boxlabel/<box_num>")
@login_required
def boxlabel(box_num):

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Invalid page access. Box number must be an integer.",
            err_page_from="/",
        )

    query_box = box_num

    ### ASSIGN QR VARIBABLES
    qr_url = "http://" + IMPS_IP + "/boxshowcontent/" + str(box_num)

    ### CALL QR LIBRARY TO MAKE THE QR IMAGE
    img = qrcode.make(qr_url)
    type(img)

    ### SAVE THE IMAGE
    save_location = "static/images/qrcodes/qr_code_for_box_" + str(box_num) + ".png"
    img.save(save_location)

    ### SET THE QR FILE LOCATION
    box_num_save_loc = [box_num, "/" + save_location]

    ### BOX NAME QUERY
    box_name_query = """ SELECT box_name FROM boxes WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box QR. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(box_name_query, (query_box,))
    result = cursor.fetchone()
    cursor.close()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Box number not in database.",
            err_page_from="/",
        )
    box_name = result[0]

    ### SHOW THE LABEL
    return render_template(
        "boxes/boxprintlabel.html",
        box_num=box_num,
        box_num_save_loc=box_num_save_loc,
        box_name=box_name,
    )


#################################################
### ADD NEW BOX FORM
@app.route("/boxadd")
@login_required
def boxadd():
    ### QUERY ALL CATEGORIES
    loc_query = "SELECT * FROM locations;"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box locations. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(loc_query)
    result = cursor.fetchall()
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box locations.",
            err_page_from="/",
        )
    locations = result
    cursor.close()
    ### QUERY BOX NUMS CURRENTLY IN USE
    available_box_nums_query = "SELECT box_num FROM boxes ORDER BY box_num;"
    cursor = mydb.cursor()
    cursor.execute(available_box_nums_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box numbers.",
            err_page_from="/",
        )

    box_nums = result
    cursor.close()

    ### TURN RESULT INTO A
    box_num_list = []
    for i in box_nums:
        box_num_list.append(i[0])
    box_nums = box_num_list

    ### FIND THE FIRST AVAILABLE BOX NUMBER
    first_available_box = None
    for i in range(len(box_nums) - 1):
        if box_nums[i + 1] - box_nums[i] > 1:
            first_available_box = box_nums[i] + 1
            break

    ### IF NO GAP ADD NEW BOX AT END OF
    if not first_available_box:
        first_available_box = len(box_nums) + 1

    ### SHOW THE ADD BOX PAGE
    return render_template(
        "boxes/boxadd.html",
        locations=locations,
        box_nums=box_nums,
        first_available_box=first_available_box,
    )


#################################################
@app.route("/boxmoveitemsconf", methods=["POST"])
@login_required
def boxmoveitems():

    ### GET FORM DATA
    old_box_num = request.form["box_to_del"]

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(old_box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Invalid entry. Box number must be an int.",
            err_page_from="/",
        )

    ### QUERY BOX NUMBERS CURRENTLY IN USE
    available_box_nums_query = "SELECT box_num FROM boxes ORDER BY box_num;"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box numbers. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(available_box_nums_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box numbers.",
            err_page_from="/",
        )
    box_nums = result

    ### TURN RESULT INTO A LIST
    box_num_list = []
    for i in box_nums:
        box_num_list.append(i[0])
    available_boxes = box_num_list

    ### SHOW THE PAGE
    return render_template(
        "boxes/boxmoveitemsconf.html",
        available_boxes=available_boxes,
        old_box_num=old_box_num,
    )


#################################################
@app.route("/boxorphanitemsconf", methods=["POST"])
@login_required
def boxorphanitems():

    ### GET FORM DATA
    box_to_del = request.form["box_to_del"]

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(box_to_del)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### QUERY BOX STATE
    box_state_query = """ SELECT * FROM items where box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when accessing box info. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(box_state_query, (box_to_del,))
    result = cursor.fetchall()
    if cursor.rowcount == 0:
        box_state = "empty"
    else:
        box_state = "not_empty"

    ### SHOW ORPHAN ITEMS PAGE
    return render_template(
        "boxes/boxorphanitemsconf.html", box_to_del=box_to_del, box_state=box_state
    )


#################################################
@app.route("/boxorphanitemssuccess", methods=["POST"])
@login_required
def boxorphanitemssuccess():

    ### GET FORM DATA
    box_to_del = request.form["box_to_del"]

    ### VERIFY VARIABLE IS AN INT
    try:
        check_int = int(box_to_del)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### ORPHAN ITEMS QUERY
    query_box = box_to_del
    orphan_query = """ UPDATE items SET box_num = NULL WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when updating box. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(orphan_query, (query_box,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not update items.",
            err_page_from="/",
        )
    cursor.close()

    ### BOX DELETE QUERY
    box_del_query = """ DELETE FROM boxes WHERE box_num = ? """
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(box_del_query, (query_box,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not delete box.",
            err_page_from="/",
        )
    mydb.commit()
    cursor.close()

    return render_template("boxes/boxorphanitemssuccess.html")


#################################################
@app.route("/boxmoveitemssuccess", methods=["POST"])
@login_required
def boxmoveitemssuccess():

    ### GET FORM DATA
    box_to_del = request.form["box_to_del"]
    new_box_num = request.form["new_box_num"]

    ### VERIFY VARIABLE IS AN INT
    try:
        check_int = int(box_to_del) + int(new_box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Invalid entry. Box number must be an int.",
            err_page_from="/",
        )

    ### MOVE ITEMS TO NEW BOX QUERY
    move_query = """UPDATE items SET box_num = ? WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error when moving items. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(move_query, (new_box_num, box_to_del))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not move items.",
            err_page_from="/",
        )
    cursor.close()

    ### DELETE BOX QUERY
    box_del_query = """ DELETE FROM boxes WHERE box_num = ? """
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(box_del_query, (box_to_del,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not delete box.",
            err_page_from="/",
        )
    mydb.commit()
    cursor.close()

    return render_template(
        "boxes/boxmoveitemssuccess.html",
        new_box_num=new_box_num,
        deleted_box=box_to_del,
    )


#################################################
### ADD BOX TO DB AND SHOW SUCCESS PAGE
@app.route("/boxadded", methods=["POST"])
@login_required
def boxadded():

    ### GET FORM DATA AND CHECK BOX NUMBER TYPE SELECTION
    if request.form["box_type"] == "next_available":
        box_num = request.form["next_num"]
    else:
        box_num = request.form["box_num"]

    ### VERIFY VARIABLE IS AN INT
    try:
        check_int = int(box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Invalid entry. Box number must be an int.",
            err_page_from="/",
        )

    ### GET ADDITIONAL FORM DATA
    next_available_box_num = request.form["next_available_box_num"]
    box_loc = request.form["box_loc"]
    box_name = request.form["box_name"]
    box_type = request.form["box_type"]

    ### IF NO CATEGORY WAS SELECTED, SET TO UNCATEGORIZED
    if box_loc == None or box_loc == "":
        box_loc == "Unspecified"

    ### IF NEXT AVAIABLE IS SET, USE THAT BOX
    if box_type == "next_available":
        box_num = next_available_box_num

    ### QUERY LOCATION NAME TO SEE IF LOCATION EXISTS
    location_query = "SELECT loc_name FROM locations"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(location_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )

    result = cursor.fetchall()
    cursor.close()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error.",
            err_page_from="/",
        )
    locations = result

    ### TURN RESULT INTO A LIST
    loc_list = []
    for i in locations:
        loc_list.append(i[0])
    locations = loc_list

    ### ADD LOCATION TO DB IF NEW
    if box_loc not in locations:
        ### SET UP ADD LOCATION QUERY
        add_loc_query = """ INSERT into locations (loc_name) VALUES (?) """
        query_loc = box_loc
        try:
            cursor = mydb.cursor(prepared=True)
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not connect to database.",
                err_page_from="/",
            )
        try:
            cursor.execute(add_loc_query, (box_loc,))
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not add location.",
                err_page_from="/",
            )

        mydb.commit()
        cursor.close()

    current_date = str(date.today())

    ### INSERT NEW BOX DATA INTO DB
    query_vars = (box_num, box_loc, box_name, current_date, current_date)
    query_string = """ INSERT INTO boxes (box_num, box_loc, box_name, box_date,\
        box_last_changed) VALUES (?,?,?,?,?) """

    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    try:
        cursor.execute(query_string, query_vars)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not add box.",
            err_page_from="/",
        )
    mydb.commit()
    cursor.close()

    ### SHOW SUCCESS PAGE
    return render_template(
        "boxes/boxadded.html", box_num=box_num, box_loc=box_loc, box_name=box_name
    )


#################################################
### DELETE BOX
@app.route("/boxdel", methods=["POST", "GET"])
@login_required
def boxdel():

    ### GET FORM DATA IF FROM BOX DEL PAGE
    if request.method == "POST":
        box_to_del = request.form["box_to_del"]

        ### VERIFY VARIABLE IS AN INT
        try:
            check_int = int(box_to_del)
        except:
            return render_template(
                "errorpage.html",
                err_message="Entry is not a number.",
                err_page_from="/",
            )

    ### IF NOT CALLED FROM BOX LIST PAGE GET BOX NUMBER
    else:
        box_to_del = ""

    ### QUERY BOX NUMBERS CURRENTLY IN USE
    available_box_nums_query = "SELECT box_num FROM boxes ORDER BY box_num;"
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(available_box_nums_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access boxes.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    cursor.close()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access available boxes",
            err_page_from="/",
        )

    box_nums = result

    ### CREATE LIST FROM RESULT
    box_num_list = []
    for i in box_nums:
        box_num_list.append(i[0])
    box_nums = box_num_list

    ### QUERY BOX NUMBERS OF BOXES THAT ARE NOT EMPTY
    not_empty_box_query = (
        "SELECT box_num FROM items WHERE item_num >0 ORDER BY box_num;"
    )
    cursor = mydb.cursor()
    try:
        cursor.execute(not_empty_box_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access boxes",
            err_page_from="/",
        )
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access list of boxes",
            err_page_from="/",
        )
    not_empty_list = result
    cursor.close()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error.",
            err_page_from="/",
        )

    ### TURN RESULT INTO A LIST
    not_empty_box_num_list = []
    for i in not_empty_list:
        not_empty_box_num_list.append(i[0])

    ### ELIMINATE DUPLICATES
    not_empty_box_num_list = list(set(not_empty_box_num_list))

    ### SHOW THE DEL BOX PAGE
    return render_template(
        "boxes/boxdel.html",
        box_nums=box_nums,
        not_empty_box_num_list=not_empty_box_num_list,
        box_to_del=box_to_del,
    )


#################################################
### DELETE BOX CONFIRM PAGE
@app.route("/delboxconf", methods=["POST"])
@login_required
def delboxconf():

    ### GET FORM DATA
    box_to_del = request.form["box_to_del"]

    ### VERIFY VARIABLE IS AN INT
    try:
        check_int = int(box_to_del)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### GET ADDITIONAL FORM DATA
    item_handling = request.form["item_handling"]

    ### CHECK IF BOX HAS CONTENTS
    box_state_query = """ SELECT * FROM items WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(box_state_query, (box_to_del,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box list.",
            err_page_from="/",
        )

    result = cursor.fetchall()

    ### DETERMINE IF BOX IS EMPTY OR NOT
    if cursor.rowcount == 0:
        box_state = "empty"
    else:
        box_state = "not_empty"
    cursor.close()

    ### SHOW THE BOX DELETE CONFIRMATION PAGE
    return render_template(
        "boxes/boxdelconfirm.html", box_state=box_state, box_to_del=box_to_del
    )


#################################################
### EDIT BOX FORM
@app.route("/boxedit")
@login_required
def boxedit():

    ### SETUP AVAILABLE BOX NUMERS QUERY
    available_box_nums_query = "SELECT boxes.box_num FROM boxes;"

    ### QUERY DB
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(available_box_nums_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box list.",
            err_page_from="/",
        )
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error.",
            err_page_from="/",
        )

    num_items = len(result)
    cursor.close()

    ### TURN RESULT INTO A LIST
    available_boxes = []
    for i in range(num_items):
        container = list(result[i])
        available_boxes.insert(1, container.pop())

    ### RETURN BOX SELECTION PAGE
    return render_template("boxes/boxedit.html", available_boxes=available_boxes)


#################################################
### SHOW BOX DETAILS
@app.route("/boxdetails", methods=["POST"])
@login_required
def boxdetails():

    ### SET UP BOX DETAILS QUERY
    box_num = request.form["box-num"]

    ### VERIFY VARIABLE IS AN INT
    try:
        check_int = int(box_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### QUERY BOX
    box_details_query = """ SELECT * FROM boxes WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(box_details_query, (box_num,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box data.",
            err_page_from="/",
        )

    result = cursor.fetchall()
    box_details = result

    ### QUERY ALL CATEGORIES
    loc_query = "SELECT * FROM locations"
    cursor = mydb.cursor()
    try:
        cursor.execute(loc_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    locations = result
    cursor.close()

    ### ASSIGN VALUES TO FORM VARIABLES
    box_num = box_details[0][0]
    box_loc = box_details[0][1]
    box_desc = box_details[0][2]

    ### SHOW BOX DETAILS
    return render_template(
        "boxes/boxdetails.html",
        box_num=box_num,
        box_desc=box_desc,
        box_loc=box_loc,
        locations=locations,
    )


#################################################
### WRITE BOX CHANGES TO DB AND SHOW SUCCESS PAGE
@app.route("/boxedited", methods=["GET", "POST"])
@login_required
def boxeditsuccess():

    ### GET FORM DATA
    box_name = request.form["box_name"]
    box_loc = request.form["box_loc"]
    box_num = request.form["box_num"]
    ### ASSIGN NEW VARIABLES FOR QUERY
    query_name = box_name
    query_num = box_num
    query_loc = box_loc
    ### CHECK IF LOCATION IS INCLUDED, IF NOT DONT UPDATE IT
    if box_loc == "":
        box_update_query = """ UPDATE boxes SET box_name = ? WHERE box_num =  ? """

        ### QUERY DB UPDATE BOX NAME ONLY
        try:
            cursor = mydb.cursor(prepared=True)
        except:
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not connect.",
                err_page_from="/",
            )
        try:
            cursor.execute(box_update_query, (query_name, query_num))
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not update box.",
                err_page_from="/",
            )
        mydb.commit()
        cursor.close()

        ### QUERY DB READ BOX LOCATION TO DISPLAY ON FORM
        box_loc_query = """ SELECT box_loc FROM boxes WHERE box_num = ? """
        cursor = mydb.cursor(prepared=True)
        cursor.execute(box_loc_query, (box_num,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not update box.",
                err_page_from="/",
            )

        box_loc = result[0]
        mydb.commit()
        cursor.close()

    ### CHECK IF BOX LOC IS INCLUDED, IF YES UPDATE IT
    else:
        box_update_query = (
            """ UPDATE boxes SET box_name = ? , box_loc = ? WHERE box_num = ? """
        )

        ### QUERY DB UPDATE BOX NAME AND CAT
        try:
            cursor = mydb.cursor(prepared=True)
        except:
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not connect.",
                err_page_from="/",
            )
        try:
            cursor.execute(box_update_query, (query_name, box_loc, query_num))
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could update box.",
                err_page_from="/",
            )

        mydb.commit()
        cursor.close()

    ### ADD THE LOCATION TO THE LOC TABLE IF IT DOESNT EXIST

    ### QUERY DB FOR LOCATIONS IN USE
    location_query = "SELECT loc_name FROM locations"
    cursor = mydb.cursor()
    cursor.execute(location_query)
    result = cursor.fetchall()
    locations = result
    ### TURN RESULT INTO A LIST
    loc_list = []
    for i in locations:
        loc_list.append(i[0])
    locations = loc_list

    ### CHECK SUBMITTED LOCATION AGAINST THE RETURNED LIST
    if box_loc not in locations and box_loc != "":
        ### SET UP ADD LOCATION QUERY AND ADD LOC TO DB
        add_loc_query = """ INSERT into locations (loc_name) VALUE (?) """
        cursor = mydb.cursor(prepared=True)
        cursor.execute(add_loc_query, (box_loc,))
        mydb.commit()

    ### SHOW SUCESS PAGE
    return render_template(
        "boxes/boxedited.html", box_name=box_name, box_loc=box_loc, box_num=box_num
    )


#################################################
### DELETE BOX FROM DB AND SHOW SUCCESS PAGE
@app.route("/boxdeletesuccess/<box_to_del>")
@login_required
def boxdeletesuccess(box_to_del):

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(box_to_del)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### QUERY TO DELETE BOX
    query_box = box_to_del
    del_box_query = """DELETE FROM boxes WHERE box_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
        cursor.execute(del_box_query, (query_box,))
        mydb.commit()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    ### QUERY TO DELETE ITEMS
    del_items_query = """ DELETE FROM items WHERE box_num = ? """
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(del_items_query, (query_box,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    mydb.commit()
    cursor.close()

    ### SHOW BOX DELETE SUCCESS PAGE
    return render_template("boxes/boxdelsuccess.html", box_to_del=box_to_del)


########################################################################
### ITEM MANAGMENT
########################################################################


#################################################
### ITEM DETAILS FORM
@app.route("/itemdetails/<item_num>")
@login_required
def itemdetails(item_num):

    ITEM_IMAGE_DIR

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### SET UP ITEM DB QUERY
    query_item = item_num
    item_query_statement = """ SELECT * FROM items WHERE item_num = ? """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(item_query_statement, (item_num,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access item.",
            err_page_from="/",
        )
    result = cursor.fetchone()
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access item.",
            err_page_from="/",
        )
    item_list = result
    item_num = item_list[0]
    item_name = item_list[1]
    item_box = item_list[2]
    item_pic = item_list[3]
    item_date = item_list[4]
    item_cat = item_list[5]
    item_desc = item_list[6]

    return render_template(
        "items/itemdetail.html",
        item_num=item_num,
        item_name=item_name,
        item_box=item_box,
        item_pic=item_pic,
        item_date=item_date,
        item_cat=item_cat,
        item_desc=item_desc,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
    )


#################################################
### SHOW THE ADD ITEM FORM
@app.route("/itemadd",  methods=["POST", "GET"])
@login_required
def itemadd():

    try:
        prov_box_num=request.form["prov_box_num"]
        prov_box_num=int(prov_box_num)
    except:
        prov_box_num =0

    ### SET UP QUERY FOR CATEGORIES
    category_query = "SELECT * FROM categories"

    ### QUERY BD
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    try:
        cursor.execute(category_query)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    available_categories = result

    ### SET UP QUERY FOR AVAILABLE BOXES
    available_box_nums_query = "SELECT boxes.box_num FROM boxes;"

    ### QUERY DB
    cursor = mydb.cursor()
    try:
        cursor.execute(available_box_nums_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box list.",
            err_page_from="/",
        )

    result = cursor.fetchall()
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )
    num_items = len(result)
    available_boxes = []
    cursor.close()

    ### CONVERT RESULT TO LIST
    for i in range(num_items):
        container = list(result[i])
        available_boxes.insert(1, container.pop())

    ### SHOW ITEM ADD PAGE

    return render_template(
        "items/itemadd.html",
        categories=available_categories,
        available_boxes=available_boxes,
        prov_box_num = prov_box_num
    )


#################################################
### EDIT ITEM FORM
@app.route("/itemedit/<item_num>")
@login_required
def itemedit(item_num):

    ITEM_IMAGE_DIR

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### SET UP ITEM DB QUERY
    query_item = item_num
    item_query_statement = """ SELECT * FROM items WHERE item_num = ? """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(item_query_statement, (item_num,))
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access items.",
            err_page_from="/",
        )

    result = cursor.fetchone()
    cursor.close()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Item number not in database.",
            err_page_from="/",
        )

    ### BREAK RESULTS INTO SEPARATE VARIABLES
    item_result = result
    item_num = item_result[0]
    item_name = item_result[1]
    box_num = item_result[2]
    item_pic = item_result[3]
    item_date = item_result[4]
    item_cat = item_result[5]
    item_desc = item_result[6]

    ### SET UP CATEGORY DB QUERY
    category_query_statement = "SELECT * FROM categories;"

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(category_query_statement)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access category list.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Category not in database.",
            err_page_from="/",
        )

    categories = result

    ### SET UP QUERY FOR AVAILABLE BOXES
    available_box_nums_query = "SELECT boxes.box_num FROM boxes;"

    ### QUERY DB
    cursor = mydb.cursor()
    try:
        cursor.execute(available_box_nums_query)
    except:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box list.",
            err_page_from="/",
        )
    result = cursor.fetchall()
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access box list.",
            err_page_from="/",
        )
    cursor.close()

    ### CHANGE RESULT NEW LIST
    num_items = len(result)
    available_boxes = []
    for i in range(num_items):
        container = list(result[i])
        available_boxes.insert(1, container.pop())
    available_boxes.sort()

    ### RETURN RESULTS PAGE
    return render_template(
        "items/itemedit.html",
        categories=categories,
        available_boxes=available_boxes,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        item_num=item_num,
        item_name=item_name,
        box_num=box_num,
        item_pic=item_pic,
        item_date=item_date,
        item_cat=item_cat,
        item_desc=item_desc,
    )


#################################################
### SUBMIT EDITED ITEM DETAILS
@app.route("/updateitem/<item_num>", methods=["GET", "POST"])
@login_required
def updateitem(item_num):

    ITEM_IMAGE_DIR

    ### VERIFY ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### IF A FORM HAS BEEN SUBMITTED, UPDATE ITEM INFO
    if request.method == "POST":

        ### GET ITEM NUMBER FROM ROUTE
        ud_item_num = item_num

        ### GET FORM DATA
        ud_item_date = request.form["item_date"]
        ud_item_name = request.form["item_name"]
        ud_item_desc = request.form["item_desc"]
        ud_box_num = request.form["box_num"]
        ud_item_cat = request.form["item_cat"]
        no_photo = request.form.get("no_photo")

        ### FORM DATA FROM HIDDEN FIELDS
        ud_passed_in_cat = request.form["passed_in_cat"]
        ud_passed_in_pic = request.form["item_pic"]

        ### HANDLE CATEGORY DATAFIELD NOT CHANGED
        if ud_item_cat == "":
            ud_item_cat = ud_passed_in_cat

        ##SET UP ITEM DB QUERY
        item_update_query = """UPDATE items SET item_name = ?, item_desc = ?, item_cat = ?,\
            item_date = ?, box_num = ? WHERE item_num = ? """

        ### WRITE ITEM VALUES TO DB
        try:
            cursor = mydb.cursor(prepared=True)
        except:
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not connect.",
                err_page_from="/",
            )
        try:
            cursor.execute(
                item_update_query,
                (
                    ud_item_name,
                    ud_item_desc,
                    ud_item_cat,
                    ud_item_date,
                    ud_box_num,
                    ud_item_num,
                ),
            )
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not update item",
                err_page_from="/",
            )
        mydb.commit()
        cursor.close()

        ################################
        ### HANDLE A NEW CATEGORY NOT IN DB

        ### SET UP CATEGORY DB QUERY
        category_query_statement = "SELECT cat_name FROM categories;"

        ### QUERY DB
        cursor = mydb.cursor(prepared=True)
        try:
            cursor.execute(category_query_statement)
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not add access categories.",
                err_page_from="/",
            )
        result = cursor.fetchall()
        if not result:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. No categories returned.",
                err_page_from="/",
            )
        categories = result

        ### CHANGE RESULT TO A LIST
        cat_list = []
        for i in categories:
            cat_list.append(i[0])
        categories = cat_list

        ### CHECK SUBMITTED CATEGORY AGAINST DB LIST
        ### AND ADD TO DB IF NOT
        if ud_item_cat not in categories:

            ### WRITE NEW CATEGORY TO DB
            add_cat_query = """ INSERT into categories (cat_name) VALUES (?) """
            cursor = mydb.cursor(prepared=True)
            try:
                cursor.execute(add_cat_query, (ud_item_cat,))
            except:
                cursor.close()
                return render_template(
                    "errorpage.html",
                    err_message="Database error. No could not add new category.",
                    err_page_from="/",
                )
            mydb.commit()
            cursor.close()

        ####################################################
        ### IMAGE HANDLING
        ####################################################

        # check that the post request contains a file
        if "file" not in request.files:
            item_pic = ud_passed_in_pic
            photo_message = "Original photo retained."

        file = request.files["file"]

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            item_pic = ud_passed_in_pic
            photo_message = "Original photo retained."

        ### IF THE FILE IS ALLOWED AND IN THE POST SAVE IT
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            photo_message = "Photo updated."

            ### ADD TIMESTAMP TO FILE NAME TO HANDLE DUPES
            pp = pathlib.PurePath(filename)
            filename = pp.stem + str(time.time()) + pp.suffix
            save_path = IMPS_PATH + ITEM_IMAGE_DIR + filename

            ### SAVE FILE
            file.save(save_path)

            ### SHRINK IMAGE TO A REASONABLE SIZE AND SAVE
            image = Image.open(save_path)
            image = ImageOps.exif_transpose(image)
            image.thumbnail((600, 600))
            image.save(save_path)

            ### DELETE FORMER PHOTO UNLESS IT IS THE PLACEHOLDER
            delete_failed = False
            if ud_passed_in_pic != "none.jpg":
                try:
                    photo_to_delete = ITEM_IMAGE_DIR[1:] + ud_passed_in_pic
                    os.remove(photo_to_delete)
                except:
                    delete_failed = True

            ### SINCE THE FILE WAS SAVED SET THE PIC TO THE NEW
            ### FILE NAME
            item_pic = filename

        ### IF A FILE IS SUBMITTED BUT THE TYPE IS PROHIBITED SHOW ERROR PAGE
        if file and not allowed_file(file.filename):
            return render_template(
                "errorpage.html",
                err_message="That file type is not allowed.",
                err_page_from="/",
            )
        ### IF NO PHOTO CHECKBOX IS SELECTED SET IMAGE TO DEFAULT
        if no_photo:
            item_pic = "none.jpg"
            photo_message = "Photo removed."

            ### ATTEMPT TO DELETE OLD PHOTO
            delete_failed = False
            if ud_passed_in_pic != "none.jpg":
                try:
                    photo_to_delete = ITEM_IMAGE_DIR[1:] + ud_passed_in_pic
                    os.remove(photo_to_delete)
                except:
                    delete_failed = True

        ### SET UP PIC QUERY
        pic_query = """ UPDATE items set item_pic = ? WHERE item_num = ?"""

        ### INSERT FILENAME INTO DB
        try:
            cursor = mydb.cursor(prepared=True)
        except:
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not connect.",
                err_page_from="/",
            )
        cursor.execute(pic_query, (item_pic, item_num))
        mydb.commit()
        cursor.close()

    ### GET ITEM PIC TO SHOW ITEM ON THE RESULTS PAGE
    ### THIS CONFIRMS THAT IT IS IN THE DATABASE
    item_query = """ SELECT item_pic FROM items WHERE item_num = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(item_query, (item_num,))
    result = cursor.fetchone()
    cursor.close()

    item_pic = result[0]

    ### SHOW ITEM PAGE
    return render_template(
        "items/itemdetail.html",
        item_name=ud_item_name,
        item_num=ud_item_num,
        box_num=ud_box_num,
        item_date=ud_item_date,
        item_cat=ud_item_cat,
        item_desc=ud_item_desc,
        item_pic=item_pic,
        photo_message=photo_message,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
    )


#################################################
### ADD ITEM TO DB AND UPLOAD AND SAVE PHOTO
@app.route("/iteminsert", methods=["POST"])
@login_required
def iteminsert():
    photoincluded = request.form["photo_yes_no"]

    if request.method == "POST" and photoincluded == "yes":
        ### CHECK THAT THE POST CONTAINS FILE DATA
        if "file" not in request.files:
            return render_template(
                "errorpage.html",
                err_message="The photo did not load.",
                err_page_from="/itemadd",
            )

        file = request.files["file"]
        ### HANDLE CASE WHERE BROWSER SUBMITS A FILE WITHOUT A NAME
        if file.filename == "":
            return render_template(
                "errorpage.html",
                err_message="No file selected",
                err_page_from="/itemadd",
            )

        ### IF THE FILE IS ALLOWED AND IN THE POST, SAVE IT
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            ### TIMESTAMP THE FILENAME TO HANDLE DUPES
            pp = pathlib.PurePath(filename)
            filename = pp.stem + str(time.time()) + pp.suffix
            save_path = IMPS_PATH + ITEM_IMAGE_DIR + filename
            file.save(save_path)

            # SHRINK IMAGE
            image = Image.open(save_path)
            image = ImageOps.exif_transpose(image)
            image.thumbnail((600, 600))
            image.save(save_path)

        ### IF THE FILE IS PROHIBITED SHOW ERROR PAGE
        else:
            return render_template(
                "errorpage.html",
                err_message="That file type is not allowed.",
                err_page_from="/itemadd",
            )
    ### IF NO FILE WAS INCLUDED USE THE DEFAULT PHOTO
    else:
        filename = ""

    ### GET DATE SO WE CAN SET ITEM DATE
    current_date = str(date.today())

    ### GET FORM DATA FOR INSERTION INTO DATABASE
    item_name = request.form["item_name"]
    box_num = request.form["box_num"]
    item_cat = request.form["item_cat"]
    item_desc = request.form["item_desc"]

    ### IF NO CATEGORY SELECTED, USE UNCATEGORIZED
    if item_cat == "":
        item_cat = "Uncategorized"

    ### IF NO FILE SELECTED, USE DEFAULT "NONE.JPG"
    if filename == "":
        item_pic = "none.jpg"

    else:
        item_pic = filename

    ### INSERT NEW ITEM INTO DATABASE
    insert_query = """ INSERT INTO items (item_name, box_num, item_pic, item_date, item_cat, item_desc) \
         VALUES ( ?, ?, ?, ?, ?, ?) """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    try:
        cursor.execute(
            insert_query,
            (item_name, box_num, item_pic, current_date, item_cat, item_desc),
        )
    except:
        close.cursor()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not add item.",
            err_page_from="/",
        )
    mydb.commit()
    cursor.close()

    ### GET THE ITEM NUMBER OF THE ITEM ADDED TO PASS
    ### TO THE RESULTS PAGE
    last_item_query = "SELECT LAST_INSERT_ID();"
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(last_item_query)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access last item.",
            err_page_from="/",
        )
    result = cursor.fetchone()
    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access last item.",
            err_page_from="/",
        )
    cursor.close()
    item_num = result[0]

    ### QUERY DATABASE FOR CATEGORIES TO CHECK AGAINST SUBMISSION
    category_query = "SELECT cat_name FROM categories"
    cursor = mydb.cursor()
    try:
        cursor.execute(category_query)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access category.",
            err_page_from="/",
        )

    ### CHANGE RESULT TO A LIST
    categories = result
    cat_list = []
    for i in categories:
        cat_list.append(i[0])
    categories = cat_list

    ### CHECK SUBMITTED CATEGORY AGAINST DB CAT LIST AND ADD TO
    ### DATABASE IF IT ISNT IN THE LIST
    if item_cat not in categories:
        ### SET UP ADD CATEGORY QUERY
        add_cat_query = """ INSERT into categories (cat_name) VALUES (?) """
        cursor = mydb.cursor(prepared=True)
        try:
            cursor.execute(add_cat_query, (item_cat,))
        except:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not access category list.",
                err_page_from="/",
            )
        mydb.commit()
        cursor.close()

    ### SHOW THE RESULTS PAGE
    return showitemdetail(str(item_num))


#################################################
### ITEM SUCCESSFULLY ADDED
@app.route("/addeditem", methods=["POST"])
@login_required
def addeditem():

    ### GET FORM DATA
    item_num = request.form["item_num"]

    ### CHECK THAT VARIABLE IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### QUERY DB FOR ITEM INFO FOR RESULTS PAGE
    item_query = """ SELECT * FROM items WHERE item_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(item_query, (item_num,))
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access item.",
            err_page_from="/",
        )
    cursor.close()

    ### RETURN RESULTS PAGE
    return render_template("search_result.html", search_result=result)


##############################################
## ITEM DETAIL PAGE (NOT EDITABLE)
@app.route("/showitemdetail/<item_num>")
@login_required
def showitemdetail(item_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    item_query = """ SELECT * FROM items WHERE item_num = ? """
    ### DB QUERY
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(item_query, (item_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access item.",
            err_page_from="/",
        )
    cursor.close()
    item_result = result

    ### SET UP VARIABLES TO SHOW ITEM DETAIL PAGE
    item_num = item_result[0]
    item_name = item_result[1]
    box_num = item_result[2]
    item_pic = item_result[3]
    item_date = item_result[4]
    item_cat = item_result[5]
    item_desc = item_result[6]

    ### RETURN RESULTS PAGE
    return render_template(
        "items/itemdetail.html",
        item_name=item_name,
        item_num=item_num,
        item_pic=item_pic,
        box_num=box_num,
        item_date=item_date,
        item_cat=item_cat,
        item_desc=item_desc,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        from_add=True,
    )


########################################################################
### SHOW ALL ITEMS IN A CATEGORY


@app.route("/itemsbycategory/<category>")
@login_required
def itembycategory(category):

    #####################################
    ############# PAGINATION
    limit = 35
    page_req = request.args.get("page")
    if page_req == None:
        offset = 0
    else:
        offset = limit * (int(page_req) - 1)

    ### QUERY FOR ITEMS IN CATEGORY
    cat_name = category
    item_by_cat_query = """ SELECT * FROM items WHERE item_cat = ? ORDER BY item_num DESC LIMIT ? OFFSET ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(item_by_cat_query, (cat_name, limit, offset))
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="There no are items in this category or this category does not exist.",
            err_page_from="/bycategory",
        )
    cursor.close()
    item_list = result

    ### QUERY FOR NUMBER OF ITEMS IN CATEGORY
    item_by_cat_query = """ SELECT COUNT(*) FROM items WHERE item_cat = ? """
    cursor = mydb.cursor(prepared=True)
    try:
        cursor.execute(item_by_cat_query, (cat_name,))
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access category list.",
            err_page_from="/",
        )

    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    cursor.close()
    total = result[0]

    #####################################
    ############# PAGINATION
    search = False
    q = request.args.get("q")
    if q:
        search = True

    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        page=page,
        total=total,
        search=search,
        per_page=35,
    )

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### GET COOKIE AND SHOW THE APPROPRAITE VIEW
    current_view = request.cookies.get("view")

    if current_view == "mobile":
        return render_template(
            "items/itemsbycat_mobile.html",
            item_list=item_list,
            ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            cat_name=cat_name,
            page=page,
            pagination=pagination,
        )
    else:
        return render_template(
            "items/itemsbycat.html",
            item_list=item_list,
            ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
            cat_name=cat_name,
            page=page,
            pagination=pagination,
            info_column=info_column,
            photo_column=photo_column,
            date_column=date_column,
            cat_column=cat_column,
            box_column=box_column,
        )


###########################################
## DELETE ITEM CONFIRMATION PAGE
@app.route("/itemdel/<item_num>")
@login_required
def itemdel(item_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### GET ITEM DATA NEEDED TO DISPLAY PAGE
    del_query = """ SELECT * FROM items WHERE item_num = ? """

    ### CHECK DB CONNECTION
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(del_query, (item_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Item number not in database.",
            err_page_from="/",
        )

    item_result = result
    cursor.close()

    ### SET VARIABLES NEEDED FOR PAGE DISPLAY
    item_num = item_result[0]
    item_name = item_result[1]
    box_num = item_result[2]
    item_pic = item_result[3]
    item_date = item_result[4]
    item_cat = item_result[5]
    item_desc = item_result[6]

    ### RETURN RESULTS PAGE
    return render_template(
        "items/itemdel.html",
        item_num=item_num,
        item_name=item_name,
        box_num=box_num,
        item_pic=item_pic,
        item_date=item_date,
        item_cat=item_cat,
        item_desc=item_desc,
    )


###########################################
@app.route("/itemdeleted/<item_to_del>")
@login_required
def itemdeleted(item_to_del):

    ITEM_IMAGE_DIR
    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(item_to_del)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )
    ### GET PHOTO FILE NAME FROM DB
    photo_file_query = """ SELECT item_pic FROM items WHERE item_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(photo_file_query, (item_to_del,))
    result = cursor.fetchone()
    cursor.close

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access photos.",
            err_page_from="/",
        )

    ### CREATE VARIABLES FOR FILE DELETION
    photo_dir = ITEM_IMAGE_DIR[1:]
    photo_filename = result[0]
    photo_file = photo_dir + result[0]

    ### ATTEMPT TO DELETE THE PHOTO UNLESS IT IS THE PLACEHOLDER
    delete_failed = False
    if photo_filename != "none.jpg":
        try:
            os.remove(photo_file)
        except:
            delete_failed = True

    ### GET ITEM NAME FOR RESULTS PAGE
    item_name_query = """ SELECT item_name FROM items WHERE item_num = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(item_name_query, (item_to_del,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access item.",
            err_page_from="/",
        )
    item_name = result[0]

    ### SET UP DELETE STATEMENT
    del_query = """ DELETE FROM items WHERE item_num = ? """

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(del_query, (item_to_del,))
    result = cursor.fetchall()
    mydb.commit()
    cursor.close()
    ### RETURN SUCCESS
    if delete_failed == True:
        return render_template(
            "errorpage.html",
            err_message="The item was deleted from the database,\
                but IMPS was unable to delete image photo file.",
            err_page_from="/",
        )
    else:
        return render_template("items/itemdelconfirm.html", item_name=item_name)


########################################################################
### CONTROL PANEL
########################################################################


###########################################
### MAIN CP PAGE
@app.route("/control_panel")
@login_required
def controlpanel():
    dbhost
    dbname
    dbuser
    dbpass
    ITEM_IMAGE_DIR
    BACKUP_DIR

    ### SET UP BACKUP QUERY
    backup_query = "SELECT value FROM `settings` WHERE name ='backup_filename'; "

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(backup_query)
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access backup settings.",
            err_page_from="/",
        )

    backup_loc = result[0]

    ### SET UP BACKUP QUERY
    backup_query = "SELECT value FROM `settings` WHERE name ='last_backup'; "

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(backup_query)
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access backup settings.",
            err_page_from="/",
        )

    last_backup = result[0]
    cursor.close
    ### OBSCURE PASSWORD
    obscure_pass = "*" * len(dbpass)

    ### SET UP ARCHIVE BACKUP QUERY
    archive_query = """SELECT value FROM `settings` WHERE set_num ='3'; """

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(archive_query)
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access backup settings.",
            err_page_from="/",
        )

    archive_loc = result[0]
    cursor.close

    return render_template(
        "control_panel/control_panel.html",
        backup_loc=backup_loc,
        archive_loc=archive_loc,
        backup_date=last_backup,
        dbhost=dbhost,
        dbname=dbname,
        dbuser=dbuser,
        dbpass=obscure_pass,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        BACKUP_DIR=BACKUP_DIR,
    )


###########################################
@app.route("/cp_dbbackup")
@login_required
def cp_dbbackup():

    ### START BACKUP PROCESS

    BACKUP_DIR

    backup_time = str(time.time())
    dumpcmd = (
        "mysqldump -u "
        + dbuser
        + " -p"
        + dbpass
        + " "
        + dbname
        + " > "
        + BACKUP_DIR
        + "/"
        + dbname
        + "-"
        + backup_time
        + ".sql"
    )

    os.system(dumpcmd)
    backup_file = BACKUP_DIR + dbname + "-" + backup_time + ".sql"
    ### SET UP BACKUP DATE QUERY
    today = str(date.today())
    backup_date_query = (
        ''' UPDATE settings SET value="''' + today + """" WHERE set_num = "2"; """
    )
    ### CONNECT TO DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    ### WRITE BACKUP DATE TO DB
    cursor.execute(backup_date_query)
    mydb.commit()
    cursor.close

    ### WRITE BACKUP FILE LOCATION TO DB
    backup_filename_query = (
        ''' UPDATE settings SET value="''' + backup_file + """" WHERE set_num ="1"; """
    )
    cursor = mydb.cursor(prepared=True)
    cursor.execute(backup_filename_query)
    mydb.commit()
    cursor.close

    ### SET UP READ BACKUP FILENAME  QUERY
    backup_query = """SELECT value FROM `settings` WHERE name ='backup_filename'; """

    ### READ BACKUP FILE FROM DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(backup_query)
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access backup settings.",
            err_page_from="/",
        )

    ### RENDER PAGE
    return render_template("control_panel/cp_dbbackup.html", backup_file=backup_file)


##########################################
@app.route("/cp_photoarchive")
@login_required
def cp_photoarchive():
    ITEM_IMAGE_DIR
    BACKUP_DIR
    ### CREATE AN ARCHIVE OF PHOTOS
    today = str(date.today())
    archive_file = BACKUP_DIR + "imps_imagearchive." + today
    archive_start_location = ITEM_IMAGE_DIR[1:]
    shutil.make_archive(archive_file, "zip", archive_start_location)

    ### QUERY TO PUT ARCHIVE DATE INTO DB
    archive_date_query = (
        ''' UPDATE settings SET value="''' + today + """" WHERE set_num = "4"; """
    )
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(archive_date_query)
    mydb.commit()
    cursor.close

    ### ADD EXTENSION TO FILENAME FOR DB WRITE
    archive_file = archive_file + ".zip"

    ### QUERY TO PUT ARCHIVE LOCATION INTO DB
    archive_file_query = (
        ''' UPDATE settings SET value="'''
        + archive_file
        + """" WHERE set_num = "3"; """
    )
    cursor.execute(archive_file_query)
    mydb.commit()
    cursor.close

    ### RETURN PAGE
    return render_template(
        "control_panel/cp_photoarchive.html", archive_file=archive_file
    )


###########################################
@app.route("/cp_categories")
@login_required
def cp_categories():

    ###################################################################################
    ### SET UP UP CATEGORIES QUERY
    cat_name_num_query = "SELECT cat_name, cat_num FROM categories ORDER BY cat_name;"

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(cat_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:

        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    num_items = len(result)
    cat_name_num = result

    ### CREATE A LIST FROM RESULT
    all_cat_nums = []
    for i in range(num_items):
        container = list(result[i])
        all_cat_nums.insert(1, container.pop())

    ### SET UP UP CATEGORIES QUERY
    category_query = "SELECT cat_name FROM categories ORDER BY cat_name;"

    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(category_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    num_items = len(result)
    all_categories = result

    ### CREATE A LIST FROM RESULT
    all_categories = []
    for i in range(num_items):
        container = list(result[i])
        all_categories.insert(1, container.pop())

    ### SETP UP ITEM PER CAT QUERY
    cats_with_items_query = "SELECT item_cat, COUNT(1) FROM items GROUP BY item_cat;"
    ### QUERY DB
    cursor = mydb.cursor(prepared=True)
    cursor.execute(cats_with_items_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    cats_with_items = result
    cursor.close()

    items_per_cat = []

    counter = -1
    for category in all_categories:
        assigned = False
        counter = counter + 1
        for item_cat in cats_with_items:
            if item_cat[0] == category:
                tuple = (category, item_cat[1], all_cat_nums[counter])
                items_per_cat.append(tuple)
                assigned = True
        if not assigned:
            tuple = (category, 0, all_cat_nums[counter])
            items_per_cat.append(tuple)

    items_per_cat.sort(key=lambda items_per_cat: items_per_cat[0])

    ### RETURN SUCCESS
    return render_template(
        "control_panel/cp_categories.html", items_per_category=items_per_cat
    )


########################################################################
@app.route("/cp_photofilescleanup")
@login_required
def cp_photofilescleanup():

    IMPS_PATH

    ### SET UP PHOTO QUERY
    photo_files_query = "SELECT item_pic FROM items;"
    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(photo_files_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access photos.",
            err_page_from="/",
        )

    file_names_in_db = result
    cursor.close()

    num_items = len(result)
    item_list = []
    ### ITERATE THROUGH RESULT AND CONCATENATE NEW LIST
    for i in range(num_items):
        container = list(result[i])
        item_list.insert(1, container.pop())
    item_list.sort()
    correct_dir = IMPS_PATH + ITEM_IMAGE_DIR
    files_in_dir = []
    files_in_dir = os.listdir(IMPS_PATH + ITEM_IMAGE_DIR)
    files_in_dir.sort()

    orphans = list(set(files_in_dir).difference(item_list))
    try:
        orphans.remove("none.jpg")
    except:
        print("error")
    return render_template(
        "control_panel/cp_photofilescleanup.html",
        file_names_in_db=item_list,
        orphans=orphans,
        num_items=num_items,
        from_cp=True,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
    )


########################################################################
@app.route("/cp_photofilesdel", methods=["POST"])
@login_required
def cp_photofilesdel():

    ### GET LIST OF FILES FROM THE FORM
    file_list = request.form.getlist("filename")
    for x in range(len(file_list)):
        print(file_list[x])

    ### SEE WHICH LIST ITEMS ARE CHECKED
    for key, value in request.form.items():
        if key.startswith("checkbox"):
            print("Key, value: ", key, value)
    checkbox_list = request.form.getlist("checkbox")
    files_to_del = []

    ### CREATE A LIST OF FILES TO DELETE
    for x in range(len(file_list)):
        if str(x + 1) in checkbox_list:
            files_to_del.append(str(file_list[x]))

    ### DELETE THE FILES
    num_items = len(files_to_del)
    for i in range(num_items):
        try:
            os.remove(IMPS_PATH + ITEM_IMAGE_DIR + files_to_del[i])
        except:
            return render_template(
                "errorpage.html",
                err_message="Some files could not be deleted.",
                err_page_from="/cp_photofilescleanup",
            )

    ### QUERY DB FOR LIST OF PHOTOS
    photo_files_query = "SELECT item_pic  FROM items;"
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(photo_files_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access files.",
            err_page_from="/",
        )

    file_names_in_db = result
    cursor.close()

    ### ITERATE THROUGH RESULT AND CONCATENATE NEW LIST
    num_items = len(result)
    item_list = []
    for i in range(num_items):
        container = list(result[i])
        item_list.insert(1, container.pop())

    ### SORT THE RESULTS
    item_list.sort()

    ### READ FILES IN IMAGE DIRECTORY AND CREATE LIST
    files_in_dir = []
    files_in_dir = os.listdir(IMPS_PATH + ITEM_IMAGE_DIR)
    files_in_dir.sort()

    ### CREATE A LIST OF IMAGES IN DIR BUT NOT IN DB
    orphans = list(set(files_in_dir).difference(item_list))
    ### EXCLUDE DEFAULT IMAGE
    try:
        orphans.remove("none.jpg")
    except:
        print("none")
    ### SHOW THE PAGE
    return render_template(
        "control_panel/cp_photofilescleanup.html",
        file_names_in_db=item_list,
        orphans=orphans,
        from_cp=True,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
    )


########################################################################
@app.route("/cp_delallorphanphotos")
@login_required
def cp_delallorphanphotos():

    ### SET UP PHOTO QUERY
    photo_files_query = "SELECT item_pic  FROM items;"

    ### QUERY DB FOR ITEM PICS
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(photo_files_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access photos.",
            err_page_from="/",
        )

    file_names_in_db = result
    cursor.close()

    ### ITERATE THROUGH RESULT AND CONCATENATE NEW LIST
    num_items = len(result)
    item_list = []
    for i in range(num_items):
        container = list(result[i])
        item_list.insert(1, container.pop())

    ### SORT THE RESULTS
    item_list.sort()

    ### READ FILES IN IMAGE DIRECTORY AND CREATE LIST
    files_in_dir = []
    files_in_dir = os.listdir(IMPS_PATH + ITEM_IMAGE_DIR)
    files_in_dir.sort()

    ### CREATE A LIST OF IMAGES IN DIR BUT NOT IN DB
    orphans = list(set(files_in_dir).difference(item_list))

    ### EXCLUDE DEFAULT IMAGE
    try:
        orphans.remove("none.jpg")
    except:
        print("none")

    ### DELETE ALL IMAGE FILES NOT IN THE DB
    for i in range(len(orphans)):
        try:
            os.remove(IMPS_PATH + ITEM_IMAGE_DIR + orphans[i])
        except:
            return render_template(
                "errorpage.html",
                err_message="Some files could not be deleted.",
                err_page_from="control_panel/cp_photofilescleanup",
            )

    ### SHOW THE PAGE
    return redirect("cp_photofilescleanup")


########################################################################
@app.route("/cp_editcat/<cat_num>")
@login_required
def cp_editcat(cat_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(cat_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Category entry is not a number.",
            err_page_from="/",
        )

    ### SET UP CATEGORY QUERY
    category_query = """ SELECT cat_name  FROM categories WHERE cat_num = ? """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access category.",
            err_page_from="/",
        )
    cursor.execute(category_query, (cat_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access category.",
            err_page_from="/",
        )
    cat_name = result[0]
    cursor.close()

    ### SHOW THE PAGE
    return render_template(
        "control_panel/cp_catedit.html", cat_name=cat_name, cat_num=cat_num
    )


########################################################################
@app.route("/cp_cateditsuccess/<cat_num>", methods=["POST"])
@login_required
def cp_cateditsuccess(cat_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(cat_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Category entry is not a number.",
            err_page_from="/",
        )

    # GET VALUES FROM FORM
    cat_num = request.form["cat_num"]
    cat_name = request.form["cat_name"]

    ### SET UP QUERY TO GET OLD NAME SO WE CAN UPDATE ITEMS
    get_old_cat_query = """ SELECT cat_name FROM categories WHERE cat_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(get_old_cat_query, (cat_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    old_cat_name = result[0]
    cursor.close()

    ### SET UP CATEGORY QUERY
    # update_cat_query = "UPDATE categories SET cat_name ='" + cat_name + "' WHERE cat_num =" + cat_num + ";"

    update_cat_query = """ UPDATE categories SET cat_name = ? WHERE cat_num = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(update_cat_query, (cat_name, cat_num))
    mydb.commit()
    cursor.close()

    ### Update all items to use the new category

    update_item_query = """ UPDATE items SET item_cat = ? WHERE item_cat = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(update_item_query, (cat_name, old_cat_name))
    mydb.commit()
    cursor.close()

    return redirect("/cp_categories")


########################################################################
@app.route("/cp_delcat/<cat_num>")
@login_required
def cp_catdel(cat_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(cat_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Category entry is not a number.",
            err_page_from="/",
        )

    ### SET UP CATEGORY QUERY
    category_query = """ SELECT cat_name  FROM categories WHERE cat_num = ? """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(category_query, (cat_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Category does not exist.",
            err_page_from="/",
        )

    cat_name = result[0]
    cursor.close()

    return render_template(
        "control_panel/cp_catdelconf.html", cat_name=cat_name, cat_num=cat_num
    )


########################################################################
@app.route("/cp_catdelsuccess/<cat_num>", methods=["POST"])
@login_required
def cp_catdelsuccess(cat_num):

    ### CHECK THAT ROUTE DECORATOR IS AN INT
    try:
        check_int = int(cat_num)
    except:
        return render_template(
            "errorpage.html",
            err_message="Entry is not a number.",
            err_page_from="/",
        )

    ### QUERY TO GET ALL CATEGORY NAMES
    get_cat_query = """ SELECT cat_name FROM categories WHERE cat_num = ? """
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(get_cat_query, (cat_num,))
    result = cursor.fetchone()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access categories.",
            err_page_from="/",
        )

    cat_name = result[0]

    ### REASSIGN ITEMS
    update_item_cat_query = (
        """ UPDATE items SET item_cat ='Uncategorized' WHERE item_cat = ? """
    )
    cursor = mydb.cursor(prepared=True)
    cursor.execute(update_item_cat_query, (cat_name,))
    mydb.commit()

    ### DELETE CATEGORY
    del_cat_query = """ DELETE FROM categories WHERE cat_name = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(del_cat_query, (cat_name,))
    mydb.commit()
    cursor.close()

    ### RETURN TO CATEGORY LIST PAGE
    return cp_categories()


########################################################################
@app.route("/cp_delallorphans")
@login_required
def cp_delallorphans():

    ITEM_IMAGE_DIR


########################################################################
@app.route("/cp_addcat", methods=["POST"])
@login_required
def cp_addcat():

    ITEM_IMAGE_DIR

    new_cat = request.form["new_cat"]
    ### SET UP ADD CATEGORY QUERY
    add_cat_query = """ INSERT INTO categories (cat_num, cat_name) VALUES (NULL, ?) """

    ### ADD CATEGORY TO DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(add_cat_query, (new_cat,))
    mydb.commit()
    cursor.close()

    ### RETURN TO CATEGORY LIST PAGE
    return cp_categories()


########################################################################
@app.route("/cp_orphaneditemscleanup")
@login_required
def cp_orphan_list():

    ### SET UP ADD CATEGORY QUERY
    find_orphans_query = """ SELECT * FROM items WHERE box_num IS NULL; """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(find_orphans_query)
    result = cursor.fetchall()
    cursor.close()

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    return render_template(
        "control_panel/cp_orphanlist.html",
        item_list=result,
        ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
        cookies=request.cookies,
        info_column=info_column,
        photo_column=photo_column,
        date_column=date_column,
        cat_column=cat_column,
        box_column=box_column,
    )


#################################################
### SWITCH ORPHAN VIEW
@app.route("/orphan_view_switch")
@login_required
def orphan_vs():

    ### SET UP ADD CATEGORY QUERY
    find_orphans_query = """ SELECT * FROM items WHERE box_num IS NULL; """

    ### QUERY DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(find_orphans_query)
    result = cursor.fetchall()
    cursor.close()

    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    ### GET COOKIE TO DETERMINE VIEW
    current_view = request.cookies.get("view")

    ### FLIP THE VIEW COOKIE AND SHOW THE APPROPRIATE VIEW
    if current_view == "mobile":
        response = make_response(
            render_template(
                "control_panel/cp_orphanlist.html",
                item_list=result,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
                cookies=request.cookies,
            )
        )
        response.set_cookie("view", "desk")
        return response
    else:
        response = make_response(
            render_template(
                "control_panel/cp_orphanlist_mobile.html",
                item_list=result,
                ITEM_IMAGE_DIR=ITEM_IMAGE_DIR,
                IMPS_PATH=IMPS_PATH,
                cookies=request.cookies,
                info_column=info_column,
                photo_column=photo_column,
                date_column=date_column,
                cat_column=cat_column,
                box_column=box_column,
            )
        )
        response.set_cookie("view", "mobile")
        return response


###########################################
@app.route("/cp_locations")
@login_required
def cp_locations():

    ### LOCATIONS QUERY
    loc_name_num_query = "SELECT loc_name FROM locations ORDER BY loc_name;"
    ### QUERY DB FOR ALL LOCATIONS
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(loc_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
    locations = result
    cursor.close()
    locations = [t[0] for t in locations]
    ### QUERY DB FOR BOXES PER LOCATION
    loc_count = []
    for loc_name in locations:
        box_by_loc_query = """ SELECT COUNT(*) FROM boxes WHERE box_loc = ?;"""
        cursor = mydb.cursor(prepared=True)
        cursor.execute(box_by_loc_query, (loc_name,))
        result = cursor.fetchone()
        loc_count.append(result[0])
    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
        cursor.close()
        loc_count.append(result[0][0])
    ### SHOW LOCATION PAGE
    return render_template(
        "control_panel/cp_locations.html", locations=locations, loc_count=loc_count
    )


########################################################################
@app.route("/cp_editloc/<loc_name>")
@login_required
def cp_editloc(loc_name):

    ### SET UP UP CATEGORIES QUERY TO VERIFY ROUTE
    loc_name_num_query = "SELECT loc_name FROM locations ORDER BY loc_name;"
    ### QUERY DB
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error accessing locations. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(loc_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )

    locations = result
    locations = [t[0] for t in locations]

    ### VERIFY ROUTE DECORATOR IS A LOCATION
    if loc_name not in locations:
        return render_template(
            "errorpage.html",
            err_message="Invalid location. The location entered is not in the database",
            err_page_from="/control_panel/cp_locations",
        )

    else:
        ### QUERY TO GET LOC NUM BASED ON VALID NAME
        loc_num_query = """SELECT loc_num FROM locations WHERE loc_name = ?;"""
        ### QUERY DB
        cursor = mydb.cursor(prepared=True)
        cursor.execute(loc_num_query, (loc_name,))
        result = cursor.fetchone()

        ### CHECK THAT QUERY SUCCEEDED
        if not result:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not access locations.",
                err_page_from="/",
            )
        loc_num = result[0]

        return render_template(
            "control_panel/cp_locedit.html",
            old_loc_name=loc_name,
            old_loc_num=loc_num,
            locations=locations,
        )


########################################################################
@app.route("/cp_addloc", methods=["POST"])
@login_required
def cp_addloc():

    ITEM_IMAGE_DIR

    new_loc = request.form["new_loc"]

    ### SET UP ADD CATEGORY QUERY
    add_loc_query = """ INSERT INTO locations (loc_num, loc_name) VALUES (NULL, ?) """

    ### ADD LOCATION TO DB
    try:
        cursor = mydb.cursor(prepared=True)
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(add_loc_query, (new_loc,))
    mydb.commit()
    cursor.close()

    ### RETURN TO LOCATION LIST PAGE
    return cp_locations()


########################################################################
@app.route("/cp_locedited/", methods=["POST"])
@login_required
def cp_locedited():

    ### GET FORM DATA
    loc_num = request.form["loc_num"]
    new_loc_name = request.form["new_loc_name"]
    old_loc_name = request.form["old_loc_name"]

    ### SET UP UP LOCATIONS QUERY TO VERIFY ROUTE
    loc_name_num_query = "SELECT loc_name FROM locations ORDER BY loc_name;"
    ### QUERY DB
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error accessing locations. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(loc_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
    locations = result
    locations = [t[0] for t in locations]
    ### VERIFY WE ARE UPDATING A KNOWN LOCATION
    if old_loc_name not in locations:
        return render_template(
            "errorpage.html",
            err_message="Invalid location. The location entered is not in the database",
            err_page_from="/cp_locations",
        )

    else:
        ### QUERY TO UPDATE LOC NAME BASED ON LOC NUMBER
        loc_update_query = """UPDATE locations SET loc_name = ? WHERE loc_num = ?;"""

        ### QUERY DB
        cursor = mydb.cursor(prepared=True)
        cursor.execute(loc_update_query, (new_loc_name, loc_num))
        mydb.commit()
        cursor.close()

    ### RETURN TO LOCATION LIST PAGE
    return cp_locations()


########################################################################
@app.route("/cp_delloc/<loc_name>")
@login_required
def cp_delloc(loc_name):

    ### SET UP UP CATEGORIES QUERY TO VERIFY ROUTE
    loc_name_num_query = "SELECT loc_name FROM locations ORDER BY loc_name;"
    ### QUERY DB
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error accessing locations. Could not connect.",
            err_page_from="/",
        )
    cursor.execute(loc_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
    locations = result
    cursor.close()
    locations = [t[0] for t in locations]

    ### VERIFY ROUTE DECORATOR IS A LOCATION
    if loc_name not in locations:
        return render_template(
            "errorpage.html",
            err_message="Invalid location. The location entered is not in the database",
            err_page_from="/control_panel/cp_locations",
        )

    else:
        ### QUERY TO GET LOC NUM BASED ON VALID NAME
        loc_num_query = """SELECT loc_num FROM locations WHERE loc_name = ?;"""

        ### QUERY DB
        cursor = mydb.cursor(prepared=True)
        cursor.execute(loc_num_query, (loc_name,))
        result = cursor.fetchone()

        ### CHECK THAT QUERY SUCCEEDED
        if not result:
            cursor.close()
            return render_template(
                "errorpage.html",
                err_message="Database error. Could not access locations.",
                err_page_from="/",
            )
        loc_num = result[0]
        cursor.close()

        return render_template(
            "control_panel/cp_locdelconf.html",
            loc_name=loc_name,
            loc_num=loc_num,
        )


########################################################################
@app.route("/cp_locdelsuccess/<loc_name>", methods=["POST"])
@login_required
def cp_locdelsuccess(loc_name):

    ### REASSIGN BOXES
    update_box_loc_query = (
        """ UPDATE boxes SET box_loc ='Unspecified' WHERE box_loc = ? """
    )
    cursor = mydb.cursor(prepared=True)
    cursor.execute(update_box_loc_query, (loc_name,))
    mydb.commit()

    ### DELETE LOCATION
    del_loc_query = """ DELETE FROM locations WHERE loc_name = ? """
    cursor = mydb.cursor(prepared=True)
    cursor.execute(del_loc_query, (loc_name,))
    mydb.commit()
    cursor.close()

    ### LOCATIONS QUERY FOR RETURN TO LOCATIONS PAGE
    loc_name_num_query = "SELECT loc_name FROM locations ORDER BY loc_name;"
    ### QUERY DB FOR ALL LOCATIONS
    try:
        cursor = mydb.cursor()
    except:
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not connect.",
            err_page_from="/",
        )

    cursor.execute(loc_name_num_query)
    result = cursor.fetchall()

    ### CHECK THAT QUERY SUCCEEDED
    if not result:
        cursor.close()
        return render_template(
            "errorpage.html",
            err_message="Database error. Could not access locations.",
            err_page_from="/",
        )
    locations = result
    cursor.close()
    locations = [t[0] for t in locations]

    ### RETURN TO LOCATION LIST PAGE
    return cp_locations()


########################################################################
@app.route("/cp_view")
@login_required
def cp_columns():
    ### READ THE COLUMN COOKIES
    info_column = request.cookies.get("info_column")
    photo_column = request.cookies.get("photo_column")
    date_column = request.cookies.get("date_column")
    cat_column = request.cookies.get("cat_column")
    box_column = request.cookies.get("box_column")

    return render_template(
        "control_panel/cp_view.html",
        info_column=info_column,
        photo_column=photo_column,
        date_column=date_column,
        cat_column=cat_column,
        box_column=box_column,
    )


########################################################################
### MAIN LOOP
########################################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=88, debug=True)
