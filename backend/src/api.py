from crypt import methods
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def drinks():

    fetch_drinks = Drink.query.all()
    if not fetch_drinks:
        abort(404)
    
    drinks = [drink.short() for drink in fetch_drinks]

    return jsonify({"success": True, "drinks": drinks}), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(payload):

    fetch_drinks = Drink.query.all()
    if not fetch_drinks:
        print(fetch_drinks)
        abort(404)
    
    drinks = [drink.long() for drink in fetch_drinks]

    return jsonify({"success": True, "drinks": drinks}), 200

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def insert_drinks(payload):

    body = request.get_json()

    if len(body) < 2:
        abort(422)

    recipe = body['recipe']
    if type(recipe) is dict:
        recipe = [recipe]
    recipe = json.dumps(recipe)

    try:
        new_drink = Drink(title=body['title'], recipe=recipe)
        new_drink.insert()
        drink = [new_drink.long()]

        return jsonify({"success": True, "drinks": drink}), 200

    except:
        db.session.rollback()
        abort(422)

    


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('post:drinks')
def update_drinks(payload, id):

    body = request.get_json()
    up_drink = Drink.query.filter(Drink.id==id).one_or_none()

    if up_drink is None:
        abort(404)
    
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    if recipe != None:
        if type(recipe) is dict:
            recipe = [recipe]
        recipe = json.dumps(recipe)

    try:
        if title != None:
            up_drink.title = body['title']

        if recipe != None:
            up_drink.recipe = recipe

        up_drink.update()

        drink = [up_drink.long()]

        return jsonify({"success": True, "drinks": drink}), 200

    except:
        db.session.rollback()
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):

    drink = Drink.query.filter(Drink.id==id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()

    except:
        db.session.rollback()
        abort(422)

    return jsonify({"success": True, "delete": drink.id}), 200


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }), 500

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404

@app.errorhandler(405)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "Method Not Allowed"
    }), 405


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code

# Barasti
# eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjFvVVRYZEpDMWx6VGdrbEFCOTlVbyJ9.eyJpc3MiOiJodHRwczovL2Rldi1qOXAxazk5NC51cy5hdXRoMC5jb20vIiwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDc5ODcxMDY5NzE1MDE3NTcxNzAiLCJhdWQiOiJjb2ZmZWVTaG9wIiwiaWF0IjoxNjYwOTMwNjYzLCJleHAiOjE2NjA5Mzc4NjMsImF6cCI6IlNGYWE0ZTR5SHZ5ak5jYVUwOTZpcXNkZVJLV05NQjNmIiwic2NvcGUiOiIiLCJwZXJtaXNzaW9ucyI6WyJnZXQ6ZHJpbmtzIiwiZ2V0OmRyaW5rcy1kZXRhaWwiXX0.mcay9hl6UTk2BfPodL8x7-KA2AKn-DfKACw9hjG5Jk2czp8KrQttilShr3sy8a4PV8mT7vADKE-jc9WEmPozNBVkWqbwkNYH-mDt309Z0LJXD_EGFfq4CDm1eEmzt-s8h4CC8CtYh1rGg9rGLvf0s3v9_rpkuv_pegkKfFSY373W7AAoLMtuZVJnDWuSwCCMORlb8NKwxuc5K4pNORjrARKRvIrn_pZtONQJYgjiUlMteBaPPEmyseRAbKcoqcqFY9StTfJntXrwlsdvgsnoS1BPASzBAwXPoApKQ6Xkuli1GsnJdy6ka7GjU6ujSZV55nS92m2SOE-O7oCoOvZjJQ




# -------------------------------------------

# Manager

# eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjFvVVRYZEpDMWx6VGdrbEFCOTlVbyJ9.eyJpc3MiOiJodHRwczovL2Rldi1qOXAxazk5NC51cy5hdXRoMC5jb20vIiwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDIyMzg5NDU0MDg4MzU0MDI1MDYiLCJhdWQiOiJjb2ZmZWVTaG9wIiwiaWF0IjoxNjYwOTI2ODAxLCJleHAiOjE2NjA5MzQwMDEsImF6cCI6IlNGYWE0ZTR5SHZ5ak5jYVUwOTZpcXNkZVJLV05NQjNmIiwic2NvcGUiOiIiLCJwZXJtaXNzaW9ucyI6WyJkZWxldGU6ZHJpbmtzIiwiZ2V0OmRyaW5rcyIsImdldDpkcmlua3MtZGV0YWlsIiwicGF0Y2g6ZHJpbmtzIiwicG9zdDpkcmlua3MiXX0.GU7SdUuVvwsl5M2HJd_yeyX2vpWsr84zp_Vf_c0_2zWHdENRDiGDre0Fmhe1sRgs2L8LbIGQtoOryTpzNqCvS99Vfws0bGbsOBWxsw_8_BAuNfaLLFtxTAyfmLxu6UBxMpm8c3pFbyM6pCoCBk6GJRIvXP-zbM41RYqaCt-nWsHTWbAvYsvLCxYO5Av-DkS1RjsKVBBCsyeJKkxoasEUJzAOBsxuBWk0tQbd0MJzgrP0A7p8EK4hJtirmXd0MhplDOWeYkupuV9rDNRs3v75ZzBFnMXZbByJ5ucrrbBmhAuCte8oFBSRmK9dqmo35VCvcaD24QQQPhPlP4Sv85c1FQ