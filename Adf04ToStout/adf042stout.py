#!/usr/bin/python
'''
Created on August 14, 2013

@author: Matt Lykins
'''
import sys
import datetime
import fractions
import re

# Scientific notation values are missing E. True means that we should add an E
missingE = True

DEBUGMODE = False

# Test whether a string can be a number
def is_number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
    
# Remove brackets and punctuation from strings
def add_e(string):
    if missingE:
        newstring = string.replace("+","e+").replace("-","e-")
    else:
        newstring = string
    return newstring

# This is the screen reached by running the program with -? or /?
def run_help():
    print("This program converts atomic data from the ADF04 format to Stout format.\n")
    print("Syntax: adf042stout.py <Filename> \n")
    print("Filename = The ADF04 file you want to process. The default is test.dat\n")


# Control the command line parameters sent to the program
if len(sys.argv) < 2:
    print("Filename not specified")
    print("Looking for test.dat")
    #sys.exit(99)
    adf04_file_name = "test.dat"
elif len(sys.argv) == 2:
    if sys.argv[1] == "-?" or sys.argv[1] == "/?":
        run_help()
        sys.exit(0)
    adf04_file_name = str(sys.argv[1])
    print("Processing %s" % adf04_file_name)  



# Determine output file names
base_name = adf04_file_name.split(".")[0]

energy_output_name = base_name + ".nrg.txt"
tp_output_name = base_name + ".tp.txt"
coll_output_name = base_name + ".coll.txt"

# Specify column position
colpos_index = 5
colpos_config = 24 #5+19
colpos_term = 34  #5+19+10
colpos_energy = 50  #5+19+10+16

# Energy Level Arrays
index = []
energy = []
configuration = []
term = []
termToken = []
statwt = []

# Radiative and Collision Data Arrays
temps = []
levhi = []
levlo = []
eina = []
colls = []
cs = []

try:
    adf04_file = open(adf04_file_name,"r")
except IOError:
    print("PROBLEM: cannot open %s" % adf04_file_name)
    sys.exit(10)
    
# We need to be able to skip the first line of the file
firstline = True
# Are we reading energy data for RadCol Data?
readEnergyData = True
# Is this a temperature line?
temperatureLine = True

for current_line in adf04_file:
    if firstline:
        firstline = False
        continue
    
    #Reading the energy level portion of the file
    if readEnergyData:    
        tempString = ""
        
        for j in range(0,colpos_index):
            tempString = tempString + current_line[j]
            
        tempIndex = tempString.strip()
            
        #print("Index = %s" % tempIndex)
                
        # -1 denotes the end of the energy level section
        if tempIndex == "-1":
            readEnergyData = False
            continue        
        
        #************************************************
        tempString = ""
        for j in range(colpos_index,colpos_config):
            tempString = tempString + current_line[j]
            
        tempConfig = tempString.strip()
            
        #print("Config = %s" % tempConfig)
        
        #************************************************
        tempString = ""
        for j in range(colpos_config,colpos_term):
            tempString = tempString + current_line[j]
            
        tempTerm = tempString.strip()
            
        #print("Term = %s" % tempTerm)
        
        #Get stat weight
        tempTermMod = tempTerm.replace('('," ").replace(')'," ")
        termToken = tempTermMod.split()
        
        tempStatWt = 2*float(termToken[len(termToken)-1])+1
        
        #print("StatWt = %s" % tempStatWt)
        
        #************************************************
        tempString = ""
        for j in range(colpos_term,colpos_energy):
            tempString = tempString + current_line[j]
            
        tempEnergy = tempString.strip()
            
        #print("Energy = %s" % tempEnergy)
       
        #************************************************
        if DEBUGMODE:
            print("DEBUG:\t%s\t%s\t%s\t%s" % (tempIndex,tempConfig,tempTerm,tempEnergy))
        
        
        # Add values to the energy level arrays
        index.append(int(tempIndex))
        configuration.append(tempConfig)
        term.append(tempTerm)
        energy.append(float(tempEnergy))
        statwt.append(tempStatWt)
        
    #**************************************************
    # Read the rest of the file. Radiative and Collision data    
    else:
        # There are no extra spaces so we can just use split instead of column positions
        line_list = current_line.split()
        
        # Again -1 denotes the end of the section
        if line_list[0].strip() == "-1":
            break
        
        if temperatureLine:
            #There are 2 values on the line other than temps
            numTemps = len(line_list)-2
            for i in range(2,len(line_list)):
                tempTemp = line_list[i]
                # Fill in the missing E for scientific notation
                tempTemp = add_e(tempTemp)
                temps.append(float(tempTemp))
                
            temperatureLine = False
        else:
            
            tempLevHi = line_list[0]
            tempLevLo = line_list[1]
            tempEina = add_e(line_list[2])
            
            #print("%s\t%s\t%s" % (tempLevLo,tempLevHi,tempEina))
            
            #The first 3 columns are levhi, levlo, and eina. the last is bethe limit
            numColls = len(line_list)-4
            
            if numColls != numTemps:
                print ("PROBLEM: The number of temps does not equal the number of collision strengths")
                sys.exit(1)
                
                
            #Reset colls array for each row in the file
            colls = []
                
            for i in range(3,len(line_list)-1):
                tempCS = line_list[i]
                tempCS = add_e(tempCS)
                colls.append(float(tempCS))
               # print("\t%s" % tempCS) 
                
            levhi.append(int(tempLevHi))
            levlo.append(int(tempLevLo))
            eina.append(float(tempEina))
            cs.append(colls)
            
adf04_file.close()

print ("Outputting to %s, %s, and %s\n" % (energy_output_name,tp_output_name,coll_output_name))

#**************Write out energy file*********************
energy_output = open(energy_output_name,"w")

# Write out the magic number at the top of the file
energy_output.write("11 10 14\n")

# Write out the index, energy, statistical weight, configuration, and term
for ndex,nrg,stwt,cfg,trm in zip(index,energy,statwt,configuration,term):
    energy_output.write("%i\t%.1f\t%i\t%s\t%s\n" % (ndex,nrg,stwt,cfg,trm))

# Write out End of Data delimiter and Reference including the current date
energy_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
energy_output.write(date_today.strftime("%Y-%m-%d"))

energy_output.close()


#**************Write out tp file*********************
tp_output = open(tp_output_name,"w")

# Write out the magic number at the top of the file
tp_output.write("11 10 14\n")

# Write out A, lo index, hi index, and Einstein A
for ndexlo,ndexhi,eina in zip(levlo,levhi,eina):
    tp_output.write("A\t%i\t%i\t%.2e\n" % (ndexlo,ndexhi,eina))

# Write out End of Data delimiter and Reference including the current date
tp_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
tp_output.write(date_today.strftime("%Y-%m-%d"))

tp_output.close()


#**************Write out coll file*********************
coll_output = open(coll_output_name,"w")

# Write out the magic number at the top of the file
coll_output.write("11 10 14\n")

# Write out the temperature line
coll_output.write("TEMP")
for i in range(0,len(temps)):
    coll_output.write("\t%.2e" % temps[i])
coll_output.write("\n")

# Write out the collision data
for i in range(0,len(cs)):
    coll_output.write("CS ELECTRON\t%i\t%i" % (levlo[i],levhi[i]))
    for j in range(0, len(cs[i])):
        coll_output.write("\t%.2e" % cs[i][j])
    coll_output.write("\n")
    
# Write out End of Data delimiter and Reference including the current date
coll_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
coll_output.write(date_today.strftime("%Y-%m-%d"))

coll_output.close()

sys.exit(0)
