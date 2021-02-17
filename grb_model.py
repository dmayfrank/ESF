from gurobipy import *

def solve_basismodell(T, S, S_neighbours, EE, EV, c, eta, ramp):
    # Model
    model = Model("optimal sizing and operation of energy system")
    
    ### initialize variables
    C = dict()              # costs
    C['v'] = dict()         # variable, operational costs
    C['f'] = dict()         # fixed, investment costs
    H = dict()              # stored hydrogen
    dH = dict()             # change of stored hydrogen
    GtP = dict()            # gas to power
    PtG = dict()            # power to gas
    ETP = dict()            # positive electricity transport
    ETN = dict()            # negative electricity transport
    HTP = dict()            # positive hydrogen transport
    HTN = dict()            # negative hydrogen transport
    ETL = dict()            # electricity transport limit
    HTL = dict()            # hydrogen transport limit
    HL = dict()             # hydrogen storage limit
    GtPL = dict()           # fuel cell power limit
    PtGL = dict()           # electrolysis power limit
    EI = dict()             # energy import
    EX = dict()             # energy export
    HI = dict()             # hydrogen import
    HX = dict()             # hydrogen export

    for t in T:
        for s in S:
            C['v'][t,s] = model.addVar(lb=-10**9,name="Cv_%s_%s" % (t,s), vtype = "c")            # variable cost in timestep t and location s

    for s in S:
        C['f'][s] = model.addVar(lb=-10**9,name="Cf_%s" % (s), vtype = "c")                       # investment cost in location s

    for t in T:
        for s in S:
            H[t,s] = model.addVar(lb=0.0, name="H_%s_%s" % (t,s), vtype = "c")          # stored hydrogen in timestep t and location s
            dH[t,s] = model.addVar(lb=-10**9,name="dH_%s_%s" % (t,s), vtype = "c")      # change of stored hydrogen in timestep t and location s
            GtP[t,s] = model.addVar(lb=0.0, name="GtP_%s_%s" % (t,s), vtype = "c")      # gas to power in timestep t and location s
            PtG[t,s] = model.addVar(lb=0.0, name="PtG_%s_%s" % (t,s), vtype = "c")      # power to gas in timestep t and location s
            EI[t,s] = model.addVar(lb=0.0, name="EI%s_%s" % (t,s), vtype = "c")         # electricity imports in timestep t and location s            
            EX[t,s] = model.addVar(lb=0.0, name="EX%s_%s" % (t,s), vtype = "c")         # electricity exports in timestep t and location s
            HI[t,s] = model.addVar(lb=0.0, name="EI%s_%s" % (t,s), vtype = "c")         # hydrogen imports in timestep t and location s            
            HX[t,s] = model.addVar(lb=0.0, name="EX%s_%s" % (t,s), vtype = "c")         # hydrogen exports in timestep t and location s 
            for s2 in S:
                if s2 != s:
                    ETP[t,(s,s2)] = model.addVar(lb=0.0,name="ETP_%s_%s_%s" % (t,s,s2), vtype = "c")   # positive electricity transport in timestep to from s1 to s2
                    HTP[t,(s,s2)] = model.addVar(lb=0.0,name="HTP_%s_%s_%s" % (t,s,s2), vtype = "c")   # positive hydrogen transport in timestep to from s1 to s2
                    ETN[t,(s,s2)] = model.addVar(lb=0.0,name="ETN_%s_%s_%s" % (t,s,s2), vtype = "c")   # negative electricity transport in timestep to from s1 to s2
                    HTN[t,(s,s2)] = model.addVar(lb=0.0,name="HTN_%s_%s_%s" % (t,s,s2), vtype = "c")   # negative hydrogen transport in timestep to from s1 to s2
        

    for s in S:
        HL[s] = model.addVar(lb=0.0, name="HL_%s" % (s), vtype = "c")                   # hydrogen storage limit at location s
        GtPL[s] = model.addVar(lb=0.0, name="GtPL_%s" % (s), vtype = "c")               # gas to power (fuel cell) limit at location s
        PtGL[s] = model.addVar(lb=0.0, name="PtGL_%s" % (s), vtype = "c")               # power to gas (electrolyzer) limit at location s
        for s2 in S:
            if s2 != s:
                ETL[(s,s2)] = model.addVar(lb=0.0, name="ETL_%s_%s" % (s,s2), vtype = "c")    # electricity transport limit between s1 and s2
                HTL[(s,s2)] = model.addVar(lb=0.0, name="HTL_%s_%s" % (s,s2), vtype = "c")    # hydrogen transport limit between s1 and s2

    model.update()                                                                      # Update the model to make variables known. From now on, no variables should be added.

    ### add constraints; equation comments refer to LP-formulation in paper, nonnegative-constraints are part of variable initialization
    for t in T:
        for s in S:
            model.addConstr( C['v'][t,s] == EE[t,s]['fossil']*c['EE_fossil'] + EE[t,s]['solar']*c['EE_solar'] \
            + EE[t,s]['wind']*c['EE_wind'] + EE[t,s]['wind_onshore']*c['EE_wind_onshore'] + EE[t,s]['wind_offshore']*c['EE_wind_offshore'] \
            + EE[t,s]['otherRE']*c['EE_otherRE'] + EE[t,s]['nuclear']*c['EE_nuclear'] \
            + EI[t,s]*c['EE_import'] - EX[t,s]*c['EE_export'] + HI[t,s]*c['H_import'] - HX[t,s]*c['H_export'] \
            + GtP[t,s]*c['GtP'] + PtG[t,s]*c['PtG'] + H[t,s]*c['H'] \
            + 0.5 * quicksum( c['ET']*ETP[t,(s,s2)] + c['HT']*HTP[t,(s,s2)] for s2 in S if s2 != s ) \
            + 0.5 * quicksum( -c['ET']*ETN[t,(s,s2)] - c['HT']*HTN[t,(s,s2)] for s2 in S if s2 != s ) )                                 # (2) - variable costs calculation

            model.addConstr( 0 == EE[t,s]['sum'] - EV[t,s] + GtP[t,s] - PtG[t,s]/eta['electrolysis'] + EI[t,s] - EX[t,s] \
            - quicksum( ETP[t,(s,s2)] - ETN[t,(s,s2)] for s2 in S if s2 != s ) )                                                        # (4) - electricity energy balance for each t and s

            model.addConstr( dH[t,s] == PtG[t,s] - GtP[t,s]/eta['fuelcell'] + HI[t,s] - HX[t,s] \
            - quicksum( HTP[t,(s,s2)] - HTN[t,(s,s2)] for s2 in S if s2 != s ) )                                                        # (5) - hydrogen energy balance for each t and s

            if t == 0:
                model.addConstr( H[t,s] == 0 )                                                                                          # (6) - no hydrogen storage at first timestep
                model.addConstr( GtP[t,s] == 0 )
            else:
                model.addConstr( H[t,s] == H[t-1,s] + dH[t,s] )                                                                         # (7) - hydrogen energy balance accross timesteps

                model.addConstr( GtP[t,s] <= GtP[t-1,s] + GtPL[s]*ramp['fuelcell'] )                                                    # (16) - ramping up time for fuelcells
                model.addConstr( GtP[t,s] >= GtP[t-1,s] - GtPL[s]*ramp['fuelcell'] )                                                    # (17) - ramping down time for fuelcells
                model.addConstr( PtG[t,s] <= PtG[t-1,s] + PtGL[s]*ramp['electrolysis'] )                                                # (18) - ramping up time for electrolyzers
                model.addConstr( PtG[t,s] >= PtG[t-1,s] - PtGL[s]*ramp['electrolysis'] )                                                # (19) - ramping down time for electrolyzers
                
            if t == T[-1]:
                model.addConstr( H[t,s] == 0 )                                                                                          # all hydrogen should be spent in the end for optimal solution (constraint not necessary, but makes optimization faster)
                

            model.addConstr( H[t,s] <= HL[s] )                                                                                          # (20) - hydrogen storage limit

            model.addConstr( GtP[t,s] <= GtPL[s] )                                                                                      # (21) - fuel cell output limit

            model.addConstr( PtG[t,s] <= PtGL[s] )                                                                                      # (22) - electrolysis output limit

            for s2 in S:
                if s2 != s:
                    model.addConstr( ETP[t,(s,s2)] <= ETL[s,s2] )                                                                       # (8) - electricity transport below capacity limit
                    model.addConstr( ETN[t,(s,s2)] <= ETL[s,s2] )                                                                       # (9) - electricity transport below capacity limit
                    model.addConstr( ETP[t,(s,s2)] - ETN[t,(s,s2)] == ETN[t,(s2,s)] - ETP[t,(s2,s)] )                                   # (10) - positive transport in one direction means negative transport in the other direction
                    model.addConstr( HTP[t,(s,s2)] <= HTL[s,s2] )                                                                       # (12) - hydrogen transport below capacity limit
                    model.addConstr( HTN[t,(s,s2)] <= HTL[s,s2] )                                                                       # (13) - hydrogen transport below capacity limit
                    model.addConstr( HTP[t,(s,s2)] - HTN[t,(s,s2)] == HTN[t,(s2,s)] - HTP[t,(s2,s)] )                                   # (14) - positive transport in one direction means negative transport in the other direction
    

    for s in S:
        model.addConstr( C['f'][s] == c['HL']*HL[s] + c['GtPL']*GtPL[s] + c['PtGL']*PtGL[s] \
        + quicksum( c['ETL']*ETL[(s,s2)] + c['HTL']*HTL[(s,s2)] for s2 in S if s2 != s ) )                                              # (3) - investment costs calculation

        for s2 in S:
            if s2 != s:
                if (s,s2) not in S_neighbours and (s2,s) not in S_neighbours:
                    model.addConstr( 0 == ETL[s,s2] )                                                                                   # (11) - no electricity transport between non-neighbours
                    model.addConstr( 0 == HTL[s,s2] )                                                                                   # (15) - no hydrogen transport between non-neighbours


    ### set objective and solve
    model.setObjective(quicksum( ( C['f'][s] + quicksum( C['v'][t,s] for t in T ) ) for s in S ), GRB.MINIMIZE)                         # (1) - objective function
    model.optimize()
    model.printQuality()
    
    ### save variables in dict to be returned by the function
    V = dict()
    V['H'] = H
    V['dH'] = dH
    V['GtP'] = GtP
    V['PtG'] = PtG
    V['EI'] = EI
    V['EX'] = EX
    V['HI'] = EI
    V['HX'] = EX
    V['ETP'] = ETP
    V['ETN'] = ETN
    V['HTP'] = HTP
    V['HTN'] = HTN
    V['HL'] = HL
    V['ETL'] = ETL
    V['HTL'] = HTL
    V['GtPL'] = GtPL
    V['PtGL'] = PtGL
    
    for V_key, _ in V.items():
        V[V_key] = {k: v.x for k, v in V[V_key].items()}                # get variables as dicts with normal values
    for C_key, _ in C.items():
        C[C_key] = {k: v.x for k, v in C[C_key].items()}                # get variables as dicts with normal values
    V['ET'] = {k: V['ETP'][k] - V['ETN'][k] for k in V['ETP'].keys()}   # get ET variable by calculating ET = ETP - ETN
    V['HT'] = {k: V['HTP'][k] - V['HTN'][k] for k in V['HTP'].keys()}   # get ET variable by calculating ET = ETP - ETN

    return model, V, C


def solve_dispatch(T, S, S_neighbours, EE, EV, c, eta, ramp,
             HTL, ETL, GtPL, PtGL, HL, H0, last_step, rolling_horizon, print_result=False):
    # Model
    model = Model("optimal operation of energy system")
    if not print_result:
        model.setParam('OutputFlag', False)
    
    ### initialize variables
    C = dict()              # costs
    C['v'] = dict()         # variable, operational costs
    C['f'] = dict()         # fixed, investment costs
    H = dict()              # stored hydrogen
    dH = dict()             # change of stored hydrogen
    GtP = dict()            # gas to power
    PtG = dict()            # power to gas
    ETP = dict()            # positive electricity transport
    ETN = dict()            # negative electricity transport
    HTP = dict()            # positive hydrogen transport
    HTN = dict()            # negative hydrogen transport
    HT = dict()             # hydrogen transport
    EI = dict()             # energy import
    EX = dict()             # energy export
    HI = dict()             # hydrogen import
    HX = dict()             # hydrogen export

    for t in T:
        for s in S:
            C['v'][t,s] = model.addVar(lb=-10**9,name="Cv_%s_%s" % (t,s), vtype = "c")            # variable cost in timestep t and location s

    for t in T:
        for s in S:
            H[t,s] = model.addVar(lb=0.0, name="H_%s_%s" % (t,s), vtype = "c")          # stored hydrogen in timestep t and location s
            dH[t,s] = model.addVar(lb=-10**9,name="dH_%s_%s" % (t,s), vtype = "c")      # change of stored hydrogen in timestep t and location s
            GtP[t,s] = model.addVar(lb=0.0, name="GtP_%s_%s" % (t,s), vtype = "c")      # gas to power in timestep t and location s
            PtG[t,s] = model.addVar(lb=0.0, name="PtG_%s_%s" % (t,s), vtype = "c")      # power to gas in timestep t and location s
            EI[t,s] = model.addVar(lb=0.0, name="EI%s_%s" % (t,s), vtype = "c")         # energy imports in timestep t and location s            
            EX[t,s] = model.addVar(lb=0.0, name="EX%s_%s" % (t,s), vtype = "c")         # energy exports in timestep t and location s
            HI[t,s] = model.addVar(lb=0.0, name="EI%s_%s" % (t,s), vtype = "c")         # hydrogen imports in timestep t and location s            
            HX[t,s] = model.addVar(lb=0.0, name="EX%s_%s" % (t,s), vtype = "c")         # hydrogen exports in timestep t and location s 
            for s2 in S:
                if s2 != s:
                    ETP[t,(s,s2)] = model.addVar(lb=0.0,name="ETP_%s_%s_%s" % (t,s,s2), vtype = "c")   # positive electricity transport in timestep to from s1 to s2
                    HTP[t,(s,s2)] = model.addVar(lb=0.0,name="HTP_%s_%s_%s" % (t,s,s2), vtype = "c")   # positive hydrogen transport in timestep to from s1 to s2
                    ETN[t,(s,s2)] = model.addVar(lb=0.0,name="ETN_%s_%s_%s" % (t,s,s2), vtype = "c")   # negative electricity transport in timestep to from s1 to s2
                    HTN[t,(s,s2)] = model.addVar(lb=0.0,name="HTN_%s_%s_%s" % (t,s,s2), vtype = "c")   # negative hydrogen transport in timestep to from s1 to s2

    model.update()                                                                      # Update the model to make variables known. From now on, no variables should be added.

    ### add constraints; equation comments refer to LP-formulation in PDF, nonnegative-constraints are part of variable initialization
    for t in T:
        for s in S:
            model.addConstr( C['v'][t,s] == EE[t,s]['fossil']*c['EE_fossil'] + EE[t,s]['solar']*c['EE_solar'] \
            + EE[t,s]['wind']*c['EE_wind'] + EE[t,s]['wind_onshore']*c['EE_wind_onshore'] + EE[t,s]['wind_offshore']*c['EE_wind_offshore'] \
            + EE[t,s]['otherRE']*c['EE_otherRE'] + EE[t,s]['nuclear']*c['EE_nuclear'] \
            + EI[t,s]*c['EE_import'] - EX[t,s]*c['EE_export'] + HI[t,s]*c['H_import'] - HX[t,s]*c['H_export'] \
            + GtP[t,s]*c['GtP'] + PtG[t,s]*c['PtG'] + H[t,s]*c['H'] \
            + 0.5 * quicksum( c['ET']*ETP[t,(s,s2)] + c['HT']*HTP[t,(s,s2)] for s2 in S if s2 != s ) \
            + 0.5 * quicksum( -c['ET']*ETN[t,(s,s2)] - c['HT']*HTN[t,(s,s2)] for s2 in S if s2 != s ) )                                 # (2) - variable costs calculation

            model.addConstr( 0 == EE[t,s]['sum'] - EV[t,s] + GtP[t,s] - PtG[t,s]/eta['electrolysis'] + EI[t,s] - EX[t,s] \
            - quicksum( ETP[t,(s,s2)] - ETN[t,(s,s2)] for s2 in S if s2 != s ) )                                                        # (4) - electricity energy balance for each t and s

            model.addConstr( dH[t,s] == PtG[t,s] - GtP[t,s]/eta['fuelcell'] + HI[t,s] - HX[t,s] \
            - quicksum( HTP[t,(s,s2)] - HTN[t,(s,s2)] for s2 in S if s2 != s ) )                                                        # (5) - hydrogen energy balance for each t and s

            if t == T[0]:
                model.addConstr( H[t,s] == H0[s] + dH[t,s] )                                                                            # (6) - hydrogen energy balance accross timesteps
            else:
                model.addConstr( H[t,s] == H[t-1,s] + dH[t,s] )                                                                         # (7) - hydrogen energy balance accross timesteps
                
                model.addConstr( GtP[t,s] <= GtP[t-1,s] + GtPL[s]*ramp['fuelcell'] )                                                    # (16) - ramping up time for fuelcells
                model.addConstr( GtP[t,s] >= GtP[t-1,s] - GtPL[s]*ramp['fuelcell'] )                                                    # (17) - ramping down time for fuelcells
                model.addConstr( PtG[t,s] <= PtG[t-1,s] + PtGL[s]*ramp['electrolysis'] )                                                # (18) - ramping up time for electrolyzers
                model.addConstr( PtG[t,s] >= PtG[t-1,s] - PtGL[s]*ramp['electrolysis'] )                                                # (19) - ramping down time for electrolyzers

            
            if last_step == True and t == T[-1]:
                model.addConstr( H[t,s] == 0 )                                                                                          # all hydrogen should be spent in the end for optimal solution

            model.addConstr( H[t,s] <= HL[s] )                                                                                          # (20) - hydrogen storage limit

            model.addConstr( GtP[t,s] <= GtPL[s] )                                                                                      # (21) - fuel cell output limit

            model.addConstr( PtG[t,s] <= PtGL[s] )                                                                                      # (22) - electrolysis output limit

            for s2 in S:
                if s2 != s:
                    model.addConstr( ETP[t,(s,s2)] <= ETL[s,s2] )                                                                       # (8) - electricity transport below capacity limit
                    model.addConstr( ETN[t,(s,s2)] <= ETL[s,s2] )                                                                       # (9) - electricity transport below capacity limit
                    model.addConstr( ETP[t,(s,s2)] - ETN[t,(s,s2)] == ETN[t,(s2,s)] - ETP[t,(s2,s)] )                                   # (10) - positive transport in one direction means negative transport in the other direction
                    model.addConstr( HTP[t,(s,s2)] <= HTL[s,s2] )                                                                       # (12) - hydrogen transport below capacity limit
                    model.addConstr( HTN[t,(s,s2)] <= HTL[s,s2] )                                                                       # (13) - hydrogen transport below capacity limit
                    model.addConstr( HTP[t,(s,s2)] - HTN[t,(s,s2)] == HTN[t,(s2,s)] - HTP[t,(s2,s)] )                                   # (14) - positive transport in one direction means negative transport in the other direction

    ### set objective and solve
    model.setObjective(quicksum( ( quicksum( C['v'][t,s] for t in T ) ) for s in S ), GRB.MINIMIZE)                                     # (1) - objective function
    model.optimize()
    
    ### save variables in dict to be returned by the function
    if last_step == True:
        V_result = dict()
        V_result['H'] = H
        V_result['dH'] = dH
        V_result['GtP'] = GtP
        V_result['PtG'] = PtG
        V_result['EI'] = EI
        V_result['EX'] = EX
        V_result['HI'] = EI
        V_result['HX'] = EX
        V_result['ETP'] = ETP
        V_result['ETN'] = ETN
        V_result['HTP'] = HTP
        V_result['HTN'] = HTN
    else:
        V = dict()
        V['H'] = H
        V['dH'] = dH
        V['GtP'] = GtP
        V['PtG'] = PtG
        V['EI'] = EI
        V['EX'] = EX
        V['HI'] = EI
        V['HX'] = EX
        V['ETP'] = ETP
        V['ETN'] = ETN
        V['HTP'] = HTP
        V['HTN'] = HTN
        V_result = dict()
        for V_key, _ in V.items():
            V_result[V_key] = dict()
            for (t,s), value in V[V_key].items():               # filter for results of first timestep
                if t == T[0]:
                    V_result[V_key][(t,s)] = value
        
    for V_key, _ in V_result.items():
        V_result[V_key] = {k: v.x for k, v in V_result[V_key].items()}                              # get variables as dicts with normal values
    V_result['ET'] = {k: V_result['ETP'][k] - V_result['ETN'][k] for k in V_result['ETP'].keys()}   # get ET variable by calculating ET = ETP - ETN
    V_result['HT'] = {k: V_result['HTP'][k] - V_result['HTN'][k] for k in V_result['HTP'].keys()}   # get ET variable by calculating ET = ETP - ETN
    
    if rolling_horizon == True:
        C = None
    else:
        for C_key, _ in C.items():
            C[C_key] = {k: v.x for k, v in C[C_key].items()}                # get variables as dicts with normal values
    
    return model, V_result, C