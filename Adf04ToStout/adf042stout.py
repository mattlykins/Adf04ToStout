#!/usr/bin/python
'''
Created on August 14, 2013

@author: Matt
'''
import sys
import datetime
import fractions
import re

# Test whether a string can be a number
def is_number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
    
# Remove brackets and punctuation from strings
def remove_junk(string):
    newstring = string.replace('?','').replace('[','').replace(']','').replace('+x','')
    return newstring

DEBUGMODE = True
ADF04StatWt = False

if len(sys.argv) != 2:
    print("Problem: You must specify the ADF04 file")
    #sys.exit(99)
    adf04_file_name = "adf04.dat"

else:
    adf04_file_name = str(sys.argv[2])


# Generate output filenames from the inputs
#path_list = energy_file_name.split('/')
#base_name = (path_list[len(path_list)-1].split('.'))[0]
#base_path = ""

#for x in path_list:
#    if x != path_list[len(path_list)-1]:
#        base_path += x + "/"

#print (path_list)
#print (base_path)


#energy_output_name = base_path + base_name + ".nrg"
#tp_output_name = base_path + base_name + ".tp"

energy_output_name = "species.nrg.txt"
tp_output_name = "species.tp.txt"
coll_output_name = "species.coll.txt"

print ("Outputting to %s, %s, and %s\n" % (energy_output_name,tp_output_name,coll_output_name))

# Specify column position
colpos_index = 5
colpos_config = 24 #5+19
colpos_term = 34  #5+19+10
colpos_energy = 50  #5+19+10+16

index = []
energy = []
configuration = []
term = []
termToken = []
statwt = []

temps = []
levhi = []
levlo = []
eina = []
colls = []
cs = []

adf04_file = open(adf04_file_name,"r")
firstline = True
readEnergyData = True
temperatureLine = True
countTrans = 0
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
            
        print("Index = %s" % tempIndex)
        
        
        if tempIndex == "-1":
            readEnergyData = False
            continue        
        
        #************************************************
        tempString = ""
        for j in range(colpos_index,colpos_config):
            tempString = tempString + current_line[j]
            
        tempConfig = tempString.strip()
            
        print("Config = %s" % tempConfig)
        
        #************************************************
        tempString = ""
        for j in range(colpos_config,colpos_term):
            tempString = tempString + current_line[j]
            
        tempTerm = tempString.strip()
            
        print("Term = %s" % tempTerm)
        
        #Get stat weight
        #PROBLEM: ADF04 supposed to have multiplicity 2s+1. Several test files list J instead
        tempTermMod = tempTerm.replace('('," ").replace(')'," ")
        termToken = tempTermMod.split()
        
        if ADF04StatWt:
            tempStatWt = termToken[len(termToken)-1]
        else:
            tempStatWt = 2*float(termToken[len(termToken)-1])+1
        
        print("StatWt = %s" % tempStatWt)
        
        #************************************************
        tempString = ""
        for j in range(colpos_term,colpos_energy):
            tempString = tempString + current_line[j]
            
        tempEnergy = tempString.strip()
            
        print("Energy = %s" % tempEnergy)
       
        #************************************************
        #if DEBUGMODE:
        #    print("FERRET:\t%s\t%s\t%s\t%s" % (tempIndex,tempConfig,tempTerm,tempEnergy))
        
        
        index.append(int(tempIndex))
        configuration.append(tempConfig)
        term.append(tempTerm)
        energy.append(float(tempEnergy))
        statwt.append(tempStatWt)
        
    #**************************************************
    # Read the rest of the file. Radiative and Collision data    
    else:
        line_list = current_line.split()
        
        if line_list[0].strip() == "-1":
            break
        
        if temperatureLine:
            numTemps = len(line_list)-2
            for i in range(2,len(line_list)):
                tempTemp = line_list[i]
                tempTemp = tempTemp.replace("+","e+").replace("-","e-")
                temps.append(float(tempTemp))
                
            temperatureLine = False
        else:
            tempLevHi = line_list[0]
            tempLevLo = line_list[1]
            tempEina = line_list[2].replace("+","e+").replace("-","e-")
            
            print("%s\t%s\t%s" % (tempLevLo,tempLevHi,tempEina))
            
            #The first 3 columns are levhi, levlo, and eina. the last is bethe limit
            numColls = len(line_list)-4
            
            if numColls != numTemps:
                print ("PROBLEM: The number of temps does not equal the number of collision strengths")
                sys.exit(1)
                
                
            #Reset colls array
            colls = []
                
            for i in range(3,len(line_list)-1):
                tempCS = line_list[i]
                tempCS = tempCS.replace("+","e+").replace("-","e-")
                colls.append(float(tempCS))
               # print("\t%s" % tempCS) 
                
            levhi.append(int(tempLevHi))
            levlo.append(int(tempLevLo))
            eina.append(float(tempEina))
            cs.append(colls)
        
        
    
    
    
    
    
    

adf04_file.close()


#**************Write out energy file*********************
energy_output = open(energy_output_name,"w")

#Write out the magic number at the top of the file
energy_output.write("11 10 14\n")

for ndex,nrg,stwt,cfg,trm in zip(index,energy,statwt,configuration,term):
    energy_output.write("%i\t%.1f\t%i\t%s\t%s\n" % (ndex,nrg,stwt,cfg,trm))


# Write out End of Data delimiter and Reference including the current date
energy_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
energy_output.write(date_today.strftime("%Y-%m-%d"))

energy_output.close()


#**************Write out tp file*********************
tp_output = open(tp_output_name,"w")

#Write out the magic number at the top of the file
tp_output.write("11 10 14\n")

for ndexlo,ndexhi,eina in zip(levlo,levhi,eina):
    tp_output.write("A\t%i\t%i\t%.2e\n" % (ndexlo,ndexhi,eina))


# Write out End of Data delimiter and Reference including the current date
tp_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
tp_output.write(date_today.strftime("%Y-%m-%d"))

tp_output.close()


#**************Write out coll file*********************
coll_output = open(coll_output_name,"w")

#Write out the magic number at the top of the file
coll_output.write("11 10 14\n")

#Write out the temperature line
coll_output.write("TEMP")
for i in range(0,len(temps)):
    coll_output.write("\t%.2e" % temps[i])
coll_output.write("\n")

for i in range(0,len(cs)):
    coll_output.write("CS ELECTRON\t%i\t%i" % (levlo[i],levhi[i]))
    for j in range(0, len(cs[i])):
        coll_output.write("\t%.2e" % cs[i][j])
    coll_output.write("\n")
    

#for ndexlo,ndexhi,eina in zip(levlo,levhi,eina):
#    coll_output.write("A\t%i\t%i\t%.2e\n" % (ndexlo,ndexhi,eina))


# Write out End of Data delimiter and Reference including the current date
coll_output.write("**************\n#Reference:\n#")
date_today = datetime.date.today()
coll_output.write(date_today.strftime("%Y-%m-%d"))

coll_output.close()





sys.exit(0)
