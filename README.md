# Pearl Pressure Controller Support and Emulator 

The PEARL pressure controller is an ISIS-designed device. 

## Pearl Pressure Controller Useful Recourses

### Technical Manual Location: 

`\\isis\shares\ISIS_Experiment_Controls\Manuals\PEARL Pressure Controller\PEARL handbook_v3_5.docx`

### LabVIEW VI Location: 

`C:\LabVIEW Modules\Instruments\PEARL\PEARL Pressure Cell Controller`

### WIKI Pages: 

https://github.com/ISISComputingGroup/IBEX/wiki/PEARL-Instrument-Details

### IOC Repository: 

https://github.com/ISISComputingGroup/EPICS-ioc/tree/master/PEARLPC


### Useful Commands:

To start EPICS environment locally, simply run the `config_env` script: 
`C:\Instrument\Apps\EPICS\config_env`

When the IOC is running, you can use the following command to checks record values:
`<epics command> %mypvprefix%PEARLPC_01:<PV record>`

To test the IOC using LEWIS emulator, execute the `run_test.bat` script located:
`master\system_tests\run_tests.bat`

Add `-a` flag to `run_test.bat` to run IOC emulator and not tests straight away if wishing to view in IBEX or check PV values when testing.


To test, use the [IOC Test Framework](https://github.com/ISISComputingGroup/EPICS-IOC_Test_Framework) and follow [README.md](https://github.com/ISISComputingGroup/EPICS-IOC_Test_Framework/blob/master/README.md) documentation to run tests or emulator.

Add `-a` flag when running using the IOC Test Framework to run the IOC emulator and not the tests straight away if wishing to view in IBEX or check PV values when testing.