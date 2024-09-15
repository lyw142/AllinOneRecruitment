"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
  --
"""

import json
import random
from flask import Blueprint, request, jsonify
from datetime import datetime
# from models import db, 
from models import Staff_Skill, db, Staff, Role, Staff, Skill, RoleSkillMapping, RoleListing, Application
from sqlalchemy import and_, desc, func
from flask import Flask
from flask_cors import CORS
import requests

# import datetime
api = Blueprint('api', __name__)
# testing CI PIPELINE


@api.route("/createjoblisting", methods=['POST'])
def createListing():
    data = request.get_json()
    # Check if the Role_Name is a string
    if not isinstance(data.get('Role_Name'), str):
        return jsonify({"error": "Role_Name must be a string"}), 400  # HTTP 400 Bad Request
    
    # Check if the Role_Name already exists in the database
    existing_role = Role.query.filter_by(Role_Name=data['Role_Name']).first()
    
    if existing_role:
        # Create a new RoleListing entry for the existing role
        role_listing = RoleListing(
            Deadline=data['Deadline'],
            Date_Posted=data['Date_Posted'],
            Country=data['Country'],
            Hiring_Manager=data['Hiring_Manager'],
            Role_ID=existing_role.Role_ID  # Use the existing role's ID
        )
        db.session.add(role_listing)
        db.session.commit()
        
        return jsonify({"message": "Role already exists, new listing created."}), 200  # HTTP 200 OK status code
    else:
        new_role = Role(
            Role_ID=random.randint(1, 1000),
            Role_Name=data['Role_Name'],
            Role_Responsibilities=data['Role_Responsibilities']
        )
        
        db.session.add(new_role)
        db.session.commit()

        new_role = Role.query.filter_by(Role_Name=data['Role_Name']).first()
        

        '''
        NEW CODE - try out
        '''
        skill_names = data['Skills']

        # Check if skill_names is a string (single skill), and if so, convert it to a list
        if isinstance(skill_names, str):
            skill_names = [skill_names]
        for skill_name in skill_names:
            # Query the Skill table to get the Skill_ID for the given Skill_Name
            skill = Skill.query.filter_by(Skill_Name=skill_name).first()

            if skill:
                skill_id = skill.Skill_ID
            else:
                # Create a new Skill object if the Skill_Name does not exist in the database
                new_skill = Skill(
                    Skill_Name=skill_name,
                    Skill_Desc=data.get('Skill_Desc', ''),  # Make sure to handle Skill_Desc properly
                    Skill_Status="Active"
                )
                db.session.add(new_skill)
                db.session.commit()

                # Retrieve the new Skill_ID
                skill_id = Skill.query.filter_by(Skill_Name=skill_name).first().Skill_ID

            new_role_skill = RoleSkillMapping(
                    Skill_ID=skill_id,
                    Role_ID=new_role.Role_ID
            )
            db.session.add(new_role_skill)
            db.session.commit()

        # Create a new RoleListing entryc
        role_listing = RoleListing(
            Deadline=data['Deadline'],
            Date_Posted=data['Date_Posted'],
            Country = data['Country'],
            Hiring_Manager=data['Hiring_Manager'],
            Role_ID=new_role.Role_ID
        )
        db.session.add(role_listing)
        db.session.commit()

        
        return jsonify({"message": "Role created successfully, Role_SKill mapped and New Listing created."}), 201  # HTTP 201 Created status code


@api.route("/openjoblistings")
def findAllOpenJobListings():
    current_date = datetime.now().date()

    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities)
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .filter(RoleListing.Deadline >= current_date)  # Filter by Deadline
        .filter(RoleListing.Date_Posted <= current_date)
        .order_by(desc(RoleListing.Date_Posted))
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    role_listings_json = []
    for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities in results:
        result1, result2 = retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
        role_listing_data = {
            "Listing_ID": role_listing.Listing_ID,
            "Deadline": str(role_listing.Deadline),
            "Date_Posted": str(role_listing.Date_Posted),
            "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilities,
            "Role_Requirements": result2,
            "Skills": result1
        }
        role_listings_json.append(role_listing_data)

    return jsonify(role_listings_json)

def retrieveAllSkillsFromRoleListing(Role_ID):
    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleSkillMapping, Skill.Skill_Name, Skill.Skill_Desc)
        .join(Role, RoleSkillMapping.Role_ID == Role.Role_ID)
        .join(Skill, RoleSkillMapping.Skill_ID == Skill.Skill_ID)
        .filter(Role.Role_ID == Role_ID)
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    skills_json = []
    skills_desc_json = []
    for skills_result in results:
        skills_json.append(skills_result.Skill_Name)
        skills_desc_json.append(skills_result.Skill_Desc)

    return skills_json,skills_desc_json

@api.route("/getRoleListing/<int:listing_id>")
def getRoleListing(listing_id):
    try:
        # Perform joins to retrieve role listings with Hiring Manager and Role Name for the specified Listing_ID
        query = (
            db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities)
            .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
            .join(Role, RoleListing.Role_ID == Role.Role_ID)
            .filter(RoleListing.Listing_ID == listing_id)  # Filter by the specified Listing_ID
            .order_by(desc(RoleListing.Date_Posted))
        )

        # Execute the query and retrieve the results
        results = query.all()

        # Convert the results into a JSON format
        role_listings_json = []
        for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities in results:
            result1, result2 = retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
            role_listing_data = {
                "Listing_ID": role_listing.Listing_ID,
                "Deadline": str(role_listing.Deadline),
                "Date_Posted": str(role_listing.Date_Posted),
                "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
                "Role_Name": role_name,
                "Role_Responsibilities": role_responsibilities,
                "Role_Requirements": result2,
                "Skills": result1,
                "Country": role_listing.Country,
            }
            role_listings_json.append(role_listing_data)

        return jsonify(role_listings_json)

    except Exception as e:
        return jsonify({"message": "Error retrieving specific role listing", "error": str(e)}), 500

@api.route("/updateRoleListing/<int:listing_id>", methods=["PUT"])
def updateRoleListing(listing_id):
    try:
        # Retrieve the role listing based on listing_id
        # role_listing = RoleListing.query.get(listing_id)
        role_listing = db.session.get(RoleListing, listing_id)

        if not role_listing:
            return jsonify({"message": "Role listing not found"}), 404

        # Get the JSON data from the request
        data = request.get_json()

        role_listing.Deadline = data["Deadline"]
        role_listing.Date_Posted = data["Date_Posted"]
        role_listing.Country = data["Country"]
        skill_ids = data["AddedSkills"]
        remove_skill = data["RemovedSkills"] # array of skills id

        #role = Role.query.get(role_listing.Role_ID)
        role = db.session.get(Role, role_listing.Role_ID)

        if role:
            role.Role_Responsibilities = data["Role_Responsibilities"]
        else:
            return jsonify({"message": "Role not found"}), 404


        for skill_id in skill_ids:
            role_skill_mapping = RoleSkillMapping(Role_ID=role_listing.Role_ID, Skill_ID=skill_id)

            db.session.add(role_skill_mapping)

        for skill_id in remove_skill:
            role_skill_mapping = RoleSkillMapping.query.filter_by(Role_ID=role_listing.Role_ID, Skill_ID=skill_id).first()
            if role_skill_mapping:
                db.session.delete(role_skill_mapping)

        db.session.commit()

        return jsonify({"message": "Role listing updated successfully"})

    except Exception as e:
        return jsonify({"message": "Error updating role listing", "error": str(e)}), 500

# filter and show closed listings
@api.route("/closedjoblistings")
def findClosedJobListings():
    current_date = datetime.now().date()

    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities)
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .filter(RoleListing.Deadline < current_date)  # Filter by Deadline
        .order_by(desc(RoleListing.Date_Posted))
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    role_listings_json = []
    for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities in results:
        result1, result2 = retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
        role_listing_data = {
            "Listing_ID": role_listing.Listing_ID,
            "Deadline": str(role_listing.Deadline),
            "Date_Posted": str(role_listing.Date_Posted),
            "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilities,
            "Role_Requirements": result2,
            "Skills": result1
        }
        role_listings_json.append(role_listing_data)

    return jsonify(role_listings_json)

@api.route("/HRopenpendingjoblistings")
def findAllOpenPendingJobListings():
    current_date = datetime.now().date()

    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities)
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .filter(RoleListing.Deadline >= current_date)
        .order_by(desc(RoleListing.Date_Posted))
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    role_listings_json = []
    for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities in results:
        result1, result2 = retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
        role_listing_data = {
            "Listing_ID": role_listing.Listing_ID,
            "Deadline": str(role_listing.Deadline),
            "Date_Posted": str(role_listing.Date_Posted),
            "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilities,
            "Role_Requirements": result2,
            "Skills": result1
        }
        role_listings_json.append(role_listing_data)

    return jsonify(role_listings_json)

#skills api endpoint (clement)
@api.route("/skills", methods=['GET'])  # Define a new endpoint for retrieving skills
def getSkills():
    try:
        # Query the database to retrieve all skills
        skills = Skill.query.all()

        # Convert the skills to a list of dictionaries
        skills_data = [{"Skill_ID": skill.Skill_ID, "Skill_Name": skill.Skill_Name, "Skill_Desc" : skill.Skill_Desc, "Skill_Status": skill.Skill_Status} for skill in skills]

        # Sort skills_data by 'Skill_Name'
        skills_data_sorted = sorted(skills_data, key=lambda skill: skill['Skill_Name'])

        # Return the sorted skills_data as a JSON response
        return jsonify(skills_data_sorted), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving list of skills", "error": str(e)}), 500

#filter by skills

@api.route("/filterRoleListingBySkill/<list_of_skill_id>")
def filterRoleListingBySkill(list_of_skill_id):
    
    selected_skill_ids = list_of_skill_id.split(',')
    
    subquery = (
        db.session.query(RoleSkillMapping.Role_ID)
        .filter(RoleSkillMapping.Skill_ID.in_(selected_skill_ids))
        .group_by(RoleSkillMapping.Role_ID)
        .having(db.func.count(RoleSkillMapping.Skill_ID.distinct()) == len(selected_skill_ids))
        .subquery()
    )

    # Query the RoleListing table to find role listings based on the subquery
    role_listings = (
        db.session.query(
            RoleListing.Listing_ID,
            RoleListing.Deadline,
            RoleListing.Date_Posted,
            RoleListing.Role_ID,
            db.func.concat(Staff.Staff_FName, " ", Staff.Staff_LName).label("Hiring_Manager_Name"),
            Role.Role_Name,
            Role.Role_Responsibilities
        )
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .join(subquery, RoleListing.Role_ID == subquery.c.Role_ID)
        .order_by(db.desc(RoleListing.Date_Posted))
        .all()
    )


    # Convert the query results into JSON format
    role_listings_json = []

    for role_listing, deadline, date_posted, role_id, hiring_manager_name, role_name, role_responsibilites in role_listings:
        result1, result2 = retrieveAllSkillsFromRoleListing(role_id)
        role_listing_data = {
            "Listing_ID": role_listing,
            "Deadline": str(deadline),
            "Date_Posted": str(date_posted),
            "Hiring_Manager": hiring_manager_name,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilites,
            "Role_Requirements" : result2,
            "Skills": result1
        }
        role_listings_json.append(role_listing_data)

    # Return the JSON response
    return jsonify(role_listings_json)

@api.route("/getStaffSkills/<int:staff_id>")
def getStaffSkills(staff_id):
    try:
        query = (
            db.session.query(Staff_Skill, Skill.Skill_Name)
            .join(Skill, Staff_Skill.Skill_ID == Skill.Skill_ID)
            .filter(Staff_Skill.Staff_ID == staff_id) 
        )

        # Execute the query and retrieve the results
        results = query.all()

        # Convert the results into a JSON format
        staff_json = []

        for staff_skill, skill_name in results:
            staff_skill_data = {
                "Skill_ID": staff_skill.Skill_ID,
                "Skill_Name": skill_name,
            }
            staff_json.append(staff_skill_data)

        return jsonify(staff_json)

    except Exception as e:
        return jsonify({"message": "Error retrieving Staff's Skill", "error": str(e)}), 500

#Login
@api.route("/login", methods=['POST'])
def login():
    try:
        data = request.get_json()

        query = (
            db.session.query(Staff)
            .filter(Staff.Email == data["Email"])
            .filter(Staff.Password == data["Password"])
            .all()
        )   

        if query:
            staff = query[0]  # Assuming only one staff member is found

            staff_data = {
                "Access_Rights": staff.Access_Rights,
                "Staff_ID": staff.Staff_ID,
                "Name": staff.Staff_FName + staff.Staff_LName
            }
            
            return jsonify(staff_data), 200
        else :
            return jsonify({
                "data": "Staff not found"
            }), 404

    except Exception as e:
        return jsonify({"message": "Error retrieving Staff information", "error": str(e)}), 500
    
"""
Apply for Open role - Create new application
"""
@api.route("/applyforopenrole", methods=["POST"])
def create_application():
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d")

    try:
        # Get the application data from the request
        application_date = formatted_date
        application_status = "Received"
        staff_id = request.json["Staff_ID"]
        listing_id = request.json["Listing_ID"]
        # Check if Staff_ID and Listing_ID are valid integers
        if not (isinstance(staff_id, int) and isinstance(listing_id, int)):
            raise ValueError("Staff_ID and Listing_ID must be integers")

        # Check if Staff_ID already exists in the Application table
        existing_application = Application.query.filter_by(Staff_ID=staff_id,Listing_ID=listing_id).first()
        if existing_application:
            error_message = "You have already applied for this job role."
            return jsonify({"error": error_message}), 400
        
        # If its a new applcation, then create a new Application object
        application = Application(application_date, application_status, staff_id, listing_id)

        # Add the Application object to the database
        db.session.add(application)
        db.session.commit()

        # Return a success response
        return jsonify({"message": "Application successfully created"}), 201
    except KeyError as e:
        # Handle the error here
        return jsonify({"error": "Missing required key: " + str(e)}), 400
    except ValueError as e:
        # Handle the error here
        return jsonify({"error": "Invalid value: " + str(e)}), 400

"""
Endpoint to get all applications
"""
@api.route("/getapplications", methods=["GET"])
def get_all_applications():

    try:
        # Get all applications from the database
        applications = Application.query.all()

        # Convert the applications to JSON
        application_json = [application.get_all_application_details() for application in applications]

        # Return the JSON response
        return jsonify(application_json)
    except Exception as e:
        # Handle the error here
        return jsonify({"error": str(e)}), 500

"""
Endpoint to get application status
"""
@api.route("/checkApplicationStatus/<int:staff_id>/<int:listing_id>", methods=["GET"])
def check_application_status(staff_id, listing_id):
    try:
        # Check if an application exists for the staff and role
        existing_application = Application.query.filter_by(Staff_ID=staff_id, Listing_ID=listing_id).first()
        has_applied = existing_application is not None

        return jsonify({"hasApplied": has_applied}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while checking application status."}), 500

#search for candidates(HR,Manager,Directors)
@api.route("/searchStaffBySkills/<list_of_skill_id>")
def searchStaffBySkills(list_of_skill_id):
    
    selected_skill_ids = list_of_skill_id.split(',')

    if not selected_skill_ids:
            return jsonify({"message": "Skill IDs are required"}), 400
    
    results = (
        db.session.query(Staff)
        .join(Staff_Skill, Staff.Staff_ID == Staff_Skill.Staff_ID)
        .filter(Staff_Skill.Skill_ID.in_(selected_skill_ids))
        .group_by(Staff.Staff_ID)
        .having(func.count(Staff_Skill.Skill_ID) == len(selected_skill_ids))
        .all()
    )

    # Convert the query results into JSON format
    staff_json = []

    for staff in results:
        staff_data = {
            "Staff_ID": staff.Staff_ID,
            "Staff_Name": staff.Staff_FName + staff.Staff_LName,
            "Staff_Email": staff.Email,
            "Current Dept" : staff.Dept,
        }
        staff_json.append(staff_data)

    # Return the JSON response
    return jsonify(staff_json)

@api.route("/getApplicationHistory/<int:staffID>", methods=["GET"])
def get_applications_history(staffID):
    try:
        staff = Staff.query.get(staffID)
        if staff is None:
            return jsonify({"error": "Staff not found"}), 404
        
        applications = Application.query.filter_by(Staff_ID=staffID).all()
        application_data = []

        for application in applications:
            app_data = application.get_all_application_details()  # Use the get_all_application_details method

            role_listing = RoleListing.query.get(app_data['Listing_ID'])
            if role_listing:
                app_data['Deadline'] = role_listing.Deadline
                app_data['Hiring_Manager'] = role_listing.Hiring_Manager
                app_data['Role_ID'] = role_listing.Role_ID
                app_data['Country'] = role_listing.Country

                role = Role.query.get(app_data['Role_ID'])
                if role:
                    app_data['Role_Name'] = role.Role_Name

            app_data['Dept'] = staff.Dept

            application_data.append(app_data)

        return jsonify(application_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def getRoleListingByID(listing_id):
        # Perform joins to retrieve role listings with Hiring Manager and Role Name for the specified Listing_ID
        query = (
            db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities)
            .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
            .join(Role, RoleListing.Role_ID == Role.Role_ID)
            .filter(RoleListing.Listing_ID == listing_id)  # Filter by the specified Listing_ID
            .order_by(desc(RoleListing.Date_Posted))
        )

        # Execute the query and retrieve the results
        results = query.all()

        # Convert the results into a JSON format
        role_listings_json = []
        for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities in results:
            result1, result2 = retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
            role_listing_data = {
                "Listing_ID": role_listing.Listing_ID,
                "Deadline": str(role_listing.Deadline),
                "Date_Posted": str(role_listing.Date_Posted),
                "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
                "Role_Name": role_name,
                "Role_Responsibilities": role_responsibilities,
                "Role_Requirements": result2,
                "Skills": result1,
                "Country": role_listing.Country,
            }
            role_listings_json.append(role_listing_data)

        return role_listings_json
    
@api.route("/getApplicantsBySkillMatch/<int:listing_id>")
def getApplicantsBySkillMatch(listing_id):
    if not listing_id:
        return jsonify({"message": "Listing ID is required"}), 400

    requiredSkill = get_required_skills_for_listing(listing_id)
    results = (
        db.session.query(Application, Staff, Role)
        .join(Staff, Application.Staff_ID == Staff.Staff_ID)
        .join(Role, Staff.Role_ID == Role.Role_ID)
        .filter(Application.Listing_ID == listing_id)
        .all()
    )

    detailsdict = {}

    if results:
        for app, staff, role in results:
            staff_skills = get_staff_skills(app.Staff_ID)  # Retrieve skills for the staff member
            # Calculate the match score
            match_score = sum(1 for skill_id, skill_name in staff_skills if skill_name in requiredSkill)

            staff_data = {
                "Application_ID": app.Application_ID,
                "Application_Date": str(app.Application_Date),
                "Application_Status": app.Application_Status,
                "Staff_ID": staff.Staff_ID,
                "Staff_Current_Role": role.Role_Name,
                "Staff_FName": staff.Staff_FName,
                "Staff_LName": staff.Staff_LName,
                "Skills": [{"Skill_ID": skill_id, "Skill_Name": skill_name} for skill_id, skill_name in staff_skills],
                "Score": match_score,
                "roleListing": getRoleListingByID(listing_id)[0]
            }
            detailsdict["Application Number: " + str(app.Application_ID)] = staff_data

    # Sort the dictionary by the "Score" values in descending order
    #sorted_data = dict(sorted(detailsdict.items(), key=lambda x: (x[1]["Score"], x[1]["Staff_FName"]), reverse=True))

    # Convert the sorted dictionary back to JSON format
    #sorted_json = json.dumps(sorted_data, indent=4)

    #return sorted_json
    # Sort the dictionary by "Score" values in descending order, and then by "Staff_FName" in ascending order
    sorted_data = dict(sorted(detailsdict.items(), key=lambda x: (x[1]["Score"], x[1]["Staff_FName"]), reverse=True))

    # Convert the sorted dictionary back to JSON format
    sorted_json = json.dumps(sorted_data, indent=4)

    return sorted_json


def get_staff_skills(staff_id):
    skills = (
        db.session.query(Staff_Skill.Skill_ID, Skill.Skill_Name)
        .join(Skill, Staff_Skill.Skill_ID == Skill.Skill_ID)
        .filter(Staff_Skill.Staff_ID == staff_id)
        .all()
    )

    return [(skill,skill_name) for skill,skill_name in skills]

def get_required_skills_for_listing(listing_id):
    results = (
        db.session.query(RoleSkillMapping.Skill_ID, Skill)
        .join(RoleListing, RoleSkillMapping.Role_ID == RoleListing.Role_ID)
        .join(Skill, RoleSkillMapping.Skill_ID == Skill.Skill_ID)
        .filter(RoleListing.Listing_ID == listing_id)
        .all()
    )

    required_skills_name = [skill_name.Skill_Name for skill, skill_name in results]

    return required_skills_name

"""
Neo endpoint 
"""
@api.route("/getstaffwithaccess>3", methods=["GET"])
def get_staff_information_above_access_3():
    staff_above_access_3 = Staff.query.filter(Staff.Access_Rights >= 3).all()
    
    if not staff_above_access_3:
        return jsonify({"message": "No staff with access rights greater than or equal to 3 found."}), 404

    # Sort staff_list by 'Role_Name'
    staff_list = sorted([staff.get_staff_details() for staff in staff_above_access_3], key=lambda x: x.get('Staff_FName'))

    return jsonify(staff_list), 200

@api.route("/getAllStaffDetails", methods=["GET"])
def getAllStaffDetails():
    try:
        # Project specific columns
        staff_details = (
            db.session.query(
                Staff.Staff_ID,
                Staff.Staff_FName,
                Staff.Staff_LName,
                Staff.Email,
                Staff.Country,
                Staff.Dept,
                Staff.Role_ID
            )
            .all()
        )
        staff_data = [
            {
                "Staff_ID": staff.Staff_ID,
                "Staff_FName": staff.Staff_FName,
                "Staff_LName": staff.Staff_LName,
                "Email": staff.Email,
                "Country": staff.Country,
                "Dept": staff.Dept,
                "Role_ID": staff.Role_ID,
            }
            for staff in staff_details
        ]

        return jsonify(staff_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@api.route("/getAllRoles", methods=["GET"])
def get_all_roles():
    try:
        roles = db.session.query(
            Role.Role_ID,
            Role.Role_Name
        ).all()

        # Sort the roles by 'Role_Name'
        sorted_roles = sorted(roles, key=lambda role: role.Role_Name)

        role_data = [
            {
                "Role_ID": role.Role_ID,
                "Role_Name": role.Role_Name,
            }
            for role in sorted_roles
        ]

        return jsonify(role_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route("/getRoleDetails/<int:role_id>", methods=["GET"])
def get_role_details(role_id):
    try:
        role_data = (
            db.session.query(Role.Role_ID, Role.Role_Responsibilities)
            .filter(Role.Role_ID == role_id)
            .first()
        )

        if not role_data:
            return jsonify({"error": "Role not found"}), 404

        role_listing_data = (
            db.session.query(RoleListing.Hiring_Manager)
            .filter(RoleListing.Role_ID == role_id)
            .first()
        )

        staff_data = [{"Staff_FName" : ""}, {"Staff_LName" : ""}]
        if role_listing_data:
            hiring_manager = role_listing_data[0]
            staff_data = (
                db.session.query(Staff.Staff_FName, Staff.Staff_LName)
                .filter(Staff.Staff_ID == hiring_manager)
                .first()
            )

        if not role_listing_data:
        #    return jsonify({"error": "Role data not found"}), 404
            hiring_manager = ""

        skill_ids = (
            db.session.query(RoleSkillMapping.Skill_ID)
            .filter(RoleSkillMapping.Role_ID == role_id)
            .all()
        )

        if not skill_ids:
            return jsonify({"error": "Skills not found for this role"}), 404

        skill_id_list = [skill_id[0] for skill_id in skill_ids]

        skill_data = (
            db.session.query(Skill.Skill_ID, Skill.Skill_Name)
            .filter(Skill.Skill_ID.in_(skill_id_list))
            .all()
        )

        response_data = {
            "Role_ID": role_data[0],  # Include the Role_ID
            "Role_Responsibilities": role_data[1],
            "Hiring_Manager": hiring_manager,
            "Staff_FName": staff_data[0],
            "Staff_LName": staff_data[1],
            "Skills": [{"Skill_ID": skill[0], "Skill_Name": skill[1]} for skill in skill_data]
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/getCreatedRoleDetails', methods=['GET'])
def get_created_role_details():
    try:
        role_ids = db.session.query(RoleListing.Role_ID).distinct().all()
        
        if not role_ids:
            return jsonify({"error": "No roles found"}), 404

        role_details = []
        for role_id in role_ids:
            role = Role.query.filter(Role.Role_ID == role_id[0]).first()
            if role:
                role_details.append({"Role_ID": role.Role_ID, "Role_Name": role.Role_Name})

        return jsonify(role_details)
    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500
    
@api.route('/getUniqueDept', methods=['GET'])
def get_unique_dept():
    try:
       # Query the Staff table to get distinct Dept values
        unique_dept = db.session.query(Staff.Dept).distinct().all()

        if not unique_dept:
            return jsonify({"error": "No unique Dept values found"}), 404

        # Extract the 'Dept' values from the list
        dept_details = [dept[0] for dept in unique_dept]

        # Sort the 'dept_details' list by 'Dept' values
        sorted_dept_details = sorted(dept_details)

        return jsonify(sorted_dept_details)

    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500

@api.route('/getUniqueCountry', methods=['GET'])
def get_unique_country():
    try:
        # Query the Staff table to get distinct Country values
        unique_country = db.session.query(Staff.Country).distinct().all()

        if not unique_country:
            return jsonify({"error": "No unique Country values found"}), 404

        country_details = [country[0] for country in unique_country]

         # Sort the 'dept_details' list by 'Dept' values
        sorted_country_details = sorted(country_details)

        return jsonify(sorted_country_details)
    
    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500

@api.route('/createjoblistingAnother', methods=['POST'])
def create_new_job_listing():
    data = request.get_json()
    
    if data:
        try:
            # Create a new RoleListing entry for the existing role
            role_listing = RoleListing(
                Deadline=data['Deadline'],
                Date_Posted=data['Date_Posted'],
                Country=data['Country'],
                Hiring_Manager=data['Hiring_Manager'],
                Role_ID=data['Role_ID']  # Use the existing role's ID
            )
            db.session.add(role_listing)
            db.session.commit()
            
            # After the entry is created, you can access its role_listing_id
            role_listing_id = role_listing.Listing_ID  # Assuming you have an id field in your RoleListing model
            
            return jsonify({"message": "New listing created.", "role_listing_id": role_listing_id}), 200  # Return the role_listing_id along with a success message
        
        except Exception as e:
            return jsonify({"error": "An error occurred"}), 500
        