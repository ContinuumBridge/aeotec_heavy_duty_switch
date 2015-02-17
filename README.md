# aeotec_heavy_duty_switch
Adaptor for Aeotec Heavy Duty Switch

This adaptor provides a service with the following characteristics:

    energy
    power
    voltage
    current
    power_factor
    connected
    temperature
    binary_sensor
    switch
  
The power characteristic changes as soon as the power consumption changes and should be used for instantaneous monitoring. Energy, voltage, current, power_factor and temperature and sampled with a minium interval of 60 seconds. The switch characteristic is used to turn the switch on and off. When the switch changes state (normally in response to the switch characterisitc, but there is also a button inside the device that can be used for manual switching), the binary_sensor characteristic changes. The connected characteristic will change to False within about two minutes if the device becomes disconnected form the Z-Wave controller. 

See [ContinuumBridge documentation](http://continuumbridge.readme.io/v1.0/docs/characteristics) for further details of characteristics and how to use them.
