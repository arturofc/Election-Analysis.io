from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import json

application = Flask(__name__)
application.config.from_object('config')
database = SQLAlchemy(application)
# render homepage with graphs
@application.route('/')
def index():
    voter = []
    gdp = []
    education = []
    state = []
    sup = []
    # queries
    voter_query = text('select v.year, turnout, white, black, hispanic, other from vep v join demographics d on v.year = d.year')
    gdp_query = text('select * from gdp where year > 1987')
    edu_query = text('select e.year, e.lessthanHS, e.HS, e.college, e.postgrad from educationperyear e join President p on e.year = (p.YearBegin-1) order by p.YearBegin asc')
    state_query = text('select * from state')
    super_query = text('select v.year, v.turnout, d.white, d.black, d.hispanic, d.other, g.income, e.lessthanHS, e.HS, e.college, e.postgrad from gdp g join vep v join demographics d join educationperyear e on (g.year = v.year) and (v.year = d.year) and (d.year = e.year)')

    result_voter = database.engine.execute(voter_query)
    for row in result_voter:
        voter.append([row[0],row[1],row[2],row[3],row[4],row[5]])

    result_gdp = database.engine.execute(gdp_query)
    for row in result_gdp:
        gdp.append([row[0],row[1]])

    result_edu = database.engine.execute(edu_query)
    for row in result_edu:
        education.append([row[0],row[1],row[2],row[3],row[4]])

    result_state = database.engine.execute(state_query)
    for row in result_state:
        state.append([row[0], row[1], row[2]])

    result_super = database.engine.execute(super_query)
    for row in result_super:
        sup.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]])

    return render_template('index.html', voter=voter, gdp=gdp, education=education, sup=sup, state=state)


# part of application which allows you to compare between elections
@application.route('/election-comparison/')
def elect_compare():
    return render_template('comparison.html')

@application.route('/election-comparison/result', methods=['POST'])
def result():
    year1 = request.form['year1']
    year2 = request.form['year2']
    sql = text('select  (t1.turnout-t2.turnout) as turnoutDiff, (t1.white-t2.white) as whiteDiff, (t1.black-t2.black) as blackDiff, (t1.hispanic-t2.hispanic) as hispanicDiff, (t1.other-t2.other) as otherDiff, (t1.income-t2.income) as incomeDiff from (select v.year, v.turnout, white, black, hispanic, other, income from vep v join demographics d join gdp g on v.year = d.year and g.year = v.year) t1 join (select v.year, v.turnout, white, black, hispanic, other, income from vep v join demographics d join gdp g on v.year = d.year and g.year = v.year) t2 where t1.year = :selection1 and t2.year = :selection2')
    result = database.engine.execute(sql, selection1 = year1, selection2 = year2)
    differences = []
    for row in result:
        differences.append([row[0],row[1],row[2],row[3],row[4],row[5]])
    return render_template('comparison_result.html', differences=differences, year1=year1, year2=year2)

# part of application which finds similar election
@application.route('/election-comparison/similar_election', methods=['POST'])
def similar_election():
    year = request.form['year']
    vep = request.form['vep']
    white = request.form['white']
    black = request.form['black']
    hispanic = request.form['hispanic']
    other = request.form['other']
    gdp = request.form['gdp']

    sql = text('select final2.year,final2.turnout, final2.white, final2.black, final2.hispanic, final2.other, final2.income, final1.name, final1.party, final1.SenateParty, final1.HouseParty from (select YearBegin-1 as year, p1.name, p2.party, SenateParty, HouseParty from President p1 join pmember p2 join controls c1 on p1.YearBegin-1 = c1.Year +1 and p1.name = p2.name) final1 join (select t2.year, t2.turnout,t2.white, t2.black, t2.hispanic, t2.other, t2.income from (select v.year, v.turnout, white, black, hispanic, other, income from vep v join demographics d join gdp g on v.year = d.year and g.year = v.year) t1 join (select v.year, v.turnout, white, black, hispanic, other, income from vep v join demographics d join gdp g on v.year = d.year and g.year = v.year) t2 where (t1.year = :year) and (abs(t1.turnout - t2.turnout) <= :vep and abs(t1.white - t2.white) <= :white and abs(t1.hispanic - t2.hispanic) <= :hispanic and abs(t1.black - t2.black) <= :black and abs(t1.other - t2.other) <= :other and abs(t1.income - t2.income) <= :gdp) order by abs(t1.turnout - t2.turnout) asc) final2 on final1.year = final2.year')
    result = database.engine.execute(sql, year = year, vep = vep, white = white, black = black, hispanic = hispanic, other = other, gdp = gdp)
    compare = []
    for row in result:
        compare.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]])
    return render_template('similar_election.html', compare=compare, year = year, vep = vep, white = white, black = black, hispanic = hispanic, other = other, gdp = gdp)

#part of application which renders congress query
@application.route('/election-comparison/congress', methods=['POST'])
def congress():
    senate = request.form['senate']
    house = request.form['house']

    sql = text('select (c2.YearBegin-1) as election_year, c2.name, c2.party, c1.SenateParty, c1.HouseParty from controls c1 join (select p1.name, p2.party, p1.YearBegin from President p1 join pmember p2 on p1.name = p2.name) c2 on (c1.HouseParty = :house) and (c1.SenateParty = :senate) and (c2.YearBegin-1 = (c1.year + 1))')
    result = database.engine.execute(sql, senate=senate, house=house)
    congress = []
    for row in result:
        congress.append([row[0],row[1],row[2],row[3],row[4]])
    return render_template('congress.html', congress=congress, senate=json.dumps(senate), house=json.dumps(house))

@application.route('/analysis/')
def analysis1():
    return render_template('analysis.html')

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
