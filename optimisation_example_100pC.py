import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import mainapp
from matplotlib import pyplot as plt
import numpy as np
from scipy.optimize import minimize
sys.path.append('../../')
from SimulationFramework.Modules.merge_two_dicts import merge_two_dicts
from SimulationFramework.Modules.constraints import *

# print('creating app')
app = QApplication(sys.argv)
# print('importing mainapp')
# print('initialise mainapp')
OM = mainapp.MainApp(app, sys.argv)
OM.show()

evaluation_solutions = {}

def optFuncChicane(args):
    OM.modify_widget('CLA-S02:CLA-S02-MAG-QUAD-01:k1l', args[0])
    OM.modify_widget('CLA-S02:CLA-S02-MAG-QUAD-02:k1l', args[1])
    OM.modify_widget('CLA-S02:CLA-S02-MAG-QUAD-03:k1l', args[2])
    OM.modify_widget('CLA-S02:CLA-S02-MAG-QUAD-04:k1l', args[3])
    OM.modify_widget('CLA-C2V:CLA-C2V-MAG-QUAD-01:k1l', args[4])
    OM.modify_widget('CLA-C2V:CLA-C2V-MAG-QUAD-02:k1l', args[5])
    OM.modify_widget('CLA-C2V:CLA-C2V-MAG-QUAD-03:k1l', args[6])
    run_id = OM.track()
    OM.clear_all_plots()
    OM.set_screen_name('CLA-C2V-MARK-01')
    beam = OM.get_beam_object_for_id(run_id)
    # twiss = OM.get_twiss_object_for_row(0)
    emitStart = beam.normalized_horizontal_emittance
    betaXStart = beam.beta_x
    betaYStart = beam.beta_y
    # print 'Start beta_x = ', betaXStart, '  beta_y = ', betaYStart, '  emit_x = ', emitStart
    OM.set_screen_name('CLA-C2V-MARK-02')
    beam = OM.get_beam_object_for_id(run_id)
    emitEnd = beam.normalized_horizontal_emittance
    betaXEnd = beam.beta_x
    betaYEnd = beam.beta_y
    betaYPenalty = betaYStart - 50 if betaYStart > 50 else 0
    etaXEnd = beam.eta_x
    etaXEnd = etaXEnd if abs(etaXEnd) > 1e-3 else 0
    etaXPEnd = beam.eta_xp
    etaXPEnd = etaXEnd if abs(etaXEnd) > 1e-3 else 0
    # print 'End beta_x = ', betaXEnd, '  beta_y = ', betaYEnd, '  emit_x = ', emitEnd
    delta = np.sqrt((1e6*abs(emitStart-emitEnd))**2 + 1*abs(betaXStart-betaXEnd)**2 + 1*abs(betaYStart-betaYEnd)**2 + 10*abs(betaYPenalty)**2 + 100*abs(etaXEnd)**2 + 100*abs(etaXPEnd)**2)
    if delta < 0.4:
        delta = 0.4
    updateOutput('Chicane delta = ' + str(delta), args)
    evaluation_solutions[str(args)] = delta
    return delta

class Callback:
    def __init__(self, tolfun, tol=1e-8):
        self._tolf = tolfun
        self._tol = tol
        self._xk_prev = None

    def __call__(self, xk):
        print('evaluation_solutions = ', evaluation_solutions)
        if float(evaluation_solutions[str(xk)]) < float(self._tol):
            return True

        self._xk_prev = xk
        return False

def setChicane(quads=None):
    evaluation_solutions = {}
    best = [OM.get_widget_value('CLA-S02:CLA-S02-MAG-QUAD-01:k1l'),
            OM.get_widget_value('CLA-S02:CLA-S02-MAG-QUAD-02:k1l'),
            OM.get_widget_value('CLA-S02:CLA-S02-MAG-QUAD-03:k1l'),
            OM.get_widget_value('CLA-S02:CLA-S02-MAG-QUAD-04:k1l'),
            OM.get_widget_value('CLA-C2V:CLA-C2V-MAG-QUAD-01:k1l'),
            OM.get_widget_value('CLA-C2V:CLA-C2V-MAG-QUAD-02:k1l'),
            OM.get_widget_value('CLA-C2V:CLA-C2V-MAG-QUAD-03:k1l'),
    ]
    if quads is not None:
        best = quads
    # cb = Callback(None, tol=0.5)
    res = minimize(optFuncChicane, best, method='nelder-mead', options={'disp': False, 'adaptive': True, 'maxiter': 10, 'xatol': 1e-3})
    return res.x

def optFuncVELA(names, values):
    global bestdelta
    try:
        [OM.modify_widget(name, val) for name, val in list(zip(names, values))]
        run_id = OM.track()
        OM.clear_all_plots()
        constraintsList = {}
        twiss = OM.get_twiss_object_for_id(run_id)
        c2v1index = list(twiss['element_name']).index('CLA-C2V-MARK-01')
        c2v2index = list(twiss['element_name']).index('CLA-C2V-MARK-02')
        ipindex = list(twiss['element_name']).index('EBT-BA1-COFFIN-FOC')
        constraintsListBA1 = {
            'BA1_max_betax': {'type': 'lessthan', 'value': twiss['beta_x_beam'][c2v2index:ipindex], 'limit': 50, 'weight': 150},
            'BA1_max_betay': {'type': 'lessthan', 'value': twiss['beta_y_beam'][c2v2index:ipindex], 'limit': 50, 'weight': 150},

            'c2v_betax': {'type': 'equalto', 'value': twiss['beta_x'][c2v1index], 'limit': twiss['beta_x'][c2v2index], 'weight': 1},
            'c2v_betay': {'type': 'equalto', 'value': twiss['beta_y'][c2v1index], 'limit': twiss['beta_y'][c2v2index], 'weight': 1},
            'c2v_alphax': {'type': 'equalto', 'value': twiss['alpha_x'][c2v1index], 'limit': twiss['alpha_x'][c2v2index], 'weight': 1},
            'c2v_alphay': {'type': 'equalto', 'value': twiss['alpha_y'][c2v1index], 'limit': twiss['alpha_y'][c2v2index], 'weight': 1},

            'ip_Sx': {'type': 'lessthan', 'value': 1e6*twiss['sigma_x'][ipindex], 'limit': 150, 'weight': 25},
            'ip_Sy': {'type': 'lessthan', 'value': 1e6*twiss['sigma_y'][ipindex], 'limit': 150, 'weight': 25},
            'ip_alphax': {'type': 'equalto', 'value': twiss['alpha_x_beam'][ipindex], 'limit': 0., 'weight': 2.5},
            'ip_alphay': {'type': 'equalto', 'value': twiss['alpha_y_beam'][ipindex], 'limit': 0., 'weight': 2.5},
            'ip_etax': {'type': 'lessthan', 'value': abs(twiss['eta_x_beam'][ipindex]), 'limit': 3e-4, 'weight': 50},
            'ip_etaxp': {'type': 'lessthan', 'value': abs(twiss['eta_xp_beam'][ipindex]), 'limit': 3e-4, 'weight': 50},
            'dump_etax': {'type': 'equalto', 'value': twiss['eta_x_beam'][-1], 'limit': 0.67, 'weight': 5000},
            'dump_betax': {'type': 'lessthan', 'value': twiss['beta_x_beam'][-1], 'limit': 10, 'weight': 1.5},
            'dump_betay': {'type': 'lessthan', 'value': twiss['beta_y_beam'][-1], 'limit': 80, 'weight': 1.5},
        }
        constraintsList = constraintsListBA1
        cons = constraintsClass()
        delta = cons.constraints(constraintsList)
        updateOutput('VELA delta = ' + str(delta))
        if delta < bestdelta:
            bestdelta = delta
            print('### New Best: ', delta)
            # print(*args, sep = ", ")
            print ('[',', '.join(map(str,values)),']')
            print(cons.constraintsList(constraintsList))
            OM.export_yaml(auto=False, filename='optimise_100pC.yaml', directory='.')
        return delta
    except Exception as e:
        print('Error!', e)
        delta = 1e6
    else:
        return delta

def setVELA(quads):
    global bestdelta
    bestdelta = 1e10
    names, best = list(zip(*quads))
    res = minimize(lambda x: optFuncVELA(names, x), best, method='nelder-mead', options={'disp': False, 'adaptive': False, 'fatol': 1e-3, 'maxiter': 100})
    return res

def optimise_Lattice(q=100, do_optimisation=False, quads=None):
    # if quadnamevalues is None:
    #     quads = np.array([
    #         1.775, -1.648, 2.219, -1.387, 5.797,-4.95, 5.714, 1.725, -1.587, 0.376, -0.39, 0.171, 0.123, -0.264, -0.959, 1.225, 1.15, 0.039, -1.334, 1.361
    #     ])
    # OM.modify_widget('generator:charge:value', q)
    if do_optimisation:
        output = setVELA(quads)
    # optFuncVELA(output.x)
    return output

def get_quads(names):
    return [[name, OM.get_widget_value(name)] for name in names]

def updateOutput(output):
    sys.stdout.write(output + '\r')
    sys.stdout.flush()
    # print(*output)

if __name__ == '__main__':
    OM.import_yaml(filename='./optimise_100pC.yaml')
    OM.modify_widget('Linac:tracking_code:value', 'Elegant')
    OM.modify_widget('generator:charge:value', 100)
    OM.modify_widget('Gun:CLA-LRG1-GUN-CAV:field_amplitude', 58.8)
    OM.modify_widget('Linac:CLA-L01-CAV:field_amplitude', 21.2)
    OM.modify_widget('Gun:CLA-LRG1-MAG-SOL-01:field_amplitude', 0.233)
    # If in ASTRA, there is an additional offset of ~ 4degrees - elegant = -8, ASTRA = -12
    OM.modify_widget('Linac:CLA-L01-CAV:phase', -5)
    quad_names = [
        'CLA-S02:CLA-S02-MAG-QUAD-01:k1l',
        'CLA-S02:CLA-S02-MAG-QUAD-02:k1l',
        'CLA-S02:CLA-S02-MAG-QUAD-03:k1l',
        'CLA-S02:CLA-S02-MAG-QUAD-04:k1l',
        'CLA-C2V:CLA-C2V-MAG-QUAD-01:k1l',
        'CLA-C2V:CLA-C2V-MAG-QUAD-02:k1l',
        'CLA-C2V:CLA-C2V-MAG-QUAD-03:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-07:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-08:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-09:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-10:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-11:k1l',
        'EBT-INJ:EBT-INJ-MAG-QUAD-15:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-01:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-02:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-03:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-04:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-05:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-06:k1l',
        'EBT-BA1:EBT-BA1-MAG-QUAD-07:k1l',
    ]
    best = get_quads(quad_names)
    # setChicane([1.775, -1.648, 2.219, -1.387, 5.797,-4.95,5.714])
    fitness = 1000
    while fitness > 10:
        output = optimise_Lattice(do_optimisation=True, quads=best)
        fitness = output.fun
        best = list(zip(quad_names, output.x))
    sys.exit(app.exec_())
