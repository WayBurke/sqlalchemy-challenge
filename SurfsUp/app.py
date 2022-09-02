#===========================================================
# PART 2: DESIGN YOUR CLIMATE APP
#===========================================================
# 1. import Flask
from flask import Flask, jsonify

# 2. import other Dependencies
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from datetime import datetime as dt
import numpy as np


#===========================================================
# 3. Database Setup
#===========================================================
# create engine to hawaii.sqlite
engine = create_engine("sqlite:///../Resources/hawaii.sqlite",echo=False, future=True)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measure = Base.classes.measurement
Station = Base.classes.station

#===========================================================
# Flask Setup and Definitions
#===========================================================

# 4. Create an app, being sure to pass __name__
app = Flask(__name__)

#-----------------------------------------------------------
# 5. Define what to do when a user hits the index route
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"List of all the available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations</br>"
        f"/api/v1.0/tobs</br>"
        f"/api/v1.0/<start></br>" #something is up with that bracket start
        f"/api/v1.0/<start>/<end></br>"
        )

#-----------------------------------------------------------
# 4. Defining the user action at each route

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # Find the most recent date in the data set.
    recent_date = session.query(Measure.date).order_by(Measure.date.desc()).first()

    # Query the data for a year's worth of data 1mth before `2017-08-23` using the datetime library
    start_date = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    last_12_mths = session.query(Measure.date, Measure.prcp).\
        filter(Measure.date <= recent_date.date).\
        filter(Measure.date >= start_date).\
        order_by(Measure.date).all()

    session.close()

    precipitation_yr =[]
    for date, prcp in last_12_mths:
        prcp_dict={}
        prcp_dict["date"]=date
        prcp_dict["prcp"]=prcp
        precipitation_yr.append(prcp_dict)

    
    return jsonify(precipitation_yr)

#-----------------------------------------------------------
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    #Create a list of distinct stations in the table
    station_list = session.query(Measure.station).distinct().all()

    # Convert list of tuples into normal list using numpy function: np.ravel()
    all_station = list(np.ravel(station_list))
    
    session.close()
    
    return jsonify(all_station)

#-----------------------------------------------------------
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

     # Find the most recent date in the data set.
    recent_date = session.query(Measure.date).order_by(Measure.date.desc()).first()

    # Query the data for a year's worth of data 1mth before `2017-08-23` using the datetime library
    start_date = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Using the most active station id from the previous query, calculate the lowest, highest, and average temperature.
    sel =[Measure.date, Measure.tobs]

    freq_station = session.query(*sel).\
        filter(Measure.station == "USC00519281").\
        filter(Measure.date <= recent_date.date).\
        filter(Measure.date >= start_date).all()

    session.close()

    freq_station_yr =[]
    for date, tobs in freq_station:
        station_dict={}
        station_dict["date"]=date
        station_dict["tobs"]=tobs
        freq_station_yr.append(station_dict)
    
    return jsonify(freq_station_yr)


#-----------------------------------------------------------
@app.route("/api/v1.0/<start>") 
def start_date(start):
    """Fetch the minimum, average, and Maximum temps for start date 
    matching the path variable supplied by the user, or a 404 if not."""

    # Create our session (link) from Python to the DB
    session = Session(engine)

    #Updating date to match what is needed
    #Date Format: yyyy-mm-dd
    corrected_start = start.replace("-","/")

    #Finding our date range in the table (first to last)
    first_date = session.query(Measure.date).order_by(Measure.date).first()
    last_date = session.query(Measure.date).order_by(Measure.date.desc()).first()

    #Canonicalized the first and last dates in the range
    can_first = first_date[0].replace("-","/")
    can_last = last_date[0].replace("-","/")
    
    #Date format
    format = '%Y/%m/%d'

    #Need to define/create dictionary of all the data, the search for the date mentioned
    # Using the date from user, calculate the lowest, highest, and average temperature.
    sel =[Measure.date,
        func.min(Measure.tobs),
        func.max(Measure.tobs),
        func.avg(Measure.tobs)
        ]

    start_date_info =[]
    
    if ((corrected_start>= can_first) &(corrected_start<= can_last)):
        #Getting all the min, max and average per date requested
        result = session.query(*sel).\
            filter(Measure.date >= dt.strptime(corrected_start,format).date()).\
            group_by(Measure.date).all()
        
        #If date is within range run the for loop to create the dictionary else return with error
        for info in result:
            date_lookup = info[0].replace("-","/")
                    
            date_dict={}
            date_dict["date"]=info[0]
            date_dict["min_temp"]=info[1]
            date_dict["max_temp"]=info[2]
            date_dict["avg_temp"]=info[3]
            start_date_info.append(date_dict)
        
        return jsonify(start_date_info)

    session.close()

    return jsonify({"Error": "Date not found, Trying entering date in this format: yyyy-mm-dd."}), 404

#-----------------------------------------------------------
@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    """Fetch the minimum, average, and Maximum temps for start date 
    matching the path variable supplied by the user, or a 404 if not."""

    # Create our session (link) from Python to the DB
    session = Session(engine)

    #Updating date to match what is needed
    #Date Format: yyyy-mm-dd
    corrected_start = start.replace("-","/")
    corrected_end = end.replace("-","/")

    #Finding our date range in the table (first to last)
    first_date = session.query(Measure.date).order_by(Measure.date).first()
    last_date = session.query(Measure.date).order_by(Measure.date.desc()).first()

    #Canonicalized the first and last dates in the table range
    can_first = first_date[0].replace("-","/")
    can_last = last_date[0].replace("-","/")
    
    #Need to define/create dictionary of all the data, the search for the date mentioned
    # Using the date from user, calculate the lowest, highest, and average temperature.
    sel =[Measure.date,
        func.min(Measure.tobs),
        func.max(Measure.tobs),
        func.avg(Measure.tobs)
        ]

    start_date_info =[]
    if(corrected_start <= corrected_end):
        if ((corrected_start>= can_first) &(corrected_end<= can_last)):
            #Getting all the min, max and average per date requested
            result = session.query(*sel).\
                filter(Measure.date >= dt.strptime(corrected_start,format).date()).\
                filter(Measure.date <= dt.strptime(corrected_end,format).date()).\
                group_by(Measure.date).all()
            
            #If date is within range run the for loop to create the dictionary else return with error
            for info in result:
                date_lookup = info[0].replace("-","/")
                        
                date_dict={}
                date_dict["date"]=info[0]
                date_dict["min_temp"]=info[1]
                date_dict["max_temp"]=info[2]
                date_dict["avg_temp"]=info[3]
                start_date_info.append(date_dict)
            
            return jsonify(start_date_info)
    else:
        return f"Your start Date is less than your end Date. Please try again"

    session.close()

    return jsonify({"Error": "Date not found, Trying entering date in this format: yyyy-mm-dd."}), 404

#-----------------------------------------------------------
# debug=True will prevent developer from having to restart server each time
if __name__ == "__main__":
    app.run(debug=True)