# -*- coding: cp1252 -*-
import random
import math

wurzeltext = ("zweite", "dritte")

def create_bpr(min_value=1, max_value=30, max_power=None):
    """Creates a base**power = result tuple and returns it.
If no max_power is given the power is never greater than 3 if
the base is above 20."""
    my_range = max_value - min_value
    base = int(round(random.random() * my_range) + min_value)
    if max_power == None:
        if base < 21: max_power = 1
        else: max_power = 0
    else:
        max_power = max_power - 2
    power = int(round(random.random() * max_power) + 2)
    result = int(round(math.pow(base, power)))
    return (base, power, result)
    

def create_power(min_value=1, max_value=30, max_power=None):
    (base, power, result) = create_bpr(min_value, max_value, max_power)
    text = "%d ^ %d" % (base, power)
    return (text, result)
        

def create_root(min_value=1, max_value=30, max_power=None):
    (base, power, result) = create_bpr(min_value, max_value, max_power)
    text = "%d sqrt %d"%(power, result)
    return (text, base)

        
def create_aufgabe(methods, parameters):
    if len(methods) == 1:
        method = methods[0]
    else:
        method_index = int(round(random.random() * (len(methods)-1)))
        method = methods[method_index]
    
    return method(parameters[0], parameters[1], parameters[2])


def loop_through_questions(methods, parameters):
    count_errors = 0
    count_questions = 0
    while True:
        (aufgabe, loesung) = create_aufgabe(methods, parameters)
        print aufgabe + " =",
        user_loesung = raw_input()
        if user_loesung.strip() == "q":
            break
        elif user_loesung.strip() == str(loesung):
            print "ok."
        else:
            print "falsch. richtige lösung: " + str(loesung)
            count_errors = count_errors + 1
        count_questions = count_questions + 1
    print "ende."
    print "%% richtig: %.4f (%d von %d)" % \
          (100 * (1.0 - float(count_errors)/count_questions), \
           count_questions - count_errors,
           count_questions)
    print "druecke ENTER"
    raw_input()



def choose_operations():
    print "min_value:",
    min_value = int(raw_input())
    print "max_value:",
    max_value = int(raw_input())
    print "max_power:",
    max_power = int(raw_input())
    print "(P)otenzieren oder (W)urzel ziehen?",
    auswahl = raw_input()
    methods = []
    parameters = (min_value, max_value, max_power)
    if len(auswahl) > 0 and auswahl[0].lower()=="p":
        methods = (create_power,)
    else:
        methods = (create_root,)
    loop_through_questions(methods, parameters)
       



def do_training():
    print "====================="
    print " Potenz-Trainer v2.0"
    print "====================="
    print "zufällig oder Auswahl (z/a) ? ",
    auswahl = raw_input()
    if len(auswahl) > 0 : auswahl = auswahl[0]
    if auswahl.lower() == "a":
        choose_operations()
    else:
        loop_through_questions(
            (create_root, create_power),
            (1,30,None))
        


if __name__=="__main__":
    random.seed()
    do_training()
