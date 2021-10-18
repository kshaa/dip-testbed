<?xml version="1.0" encoding="UTF-8"?>
<drawing version="7">
    <attr value="spartan6" name="DeviceFamilyName">
        <trait delete="all:0" />
        <trait editname="all:0" />
        <trait edittrait="all:0" />
    </attr>
    <netlist>
        <signal name="T19" />
        <signal name="XLXN_2" />
        <signal name="LD0" />
        <signal name="SW0" />
        <signal name="XLXN_7" />
        <signal name="T20" />
        <port polarity="Input" name="T19" />
        <port polarity="Output" name="LD0" />
        <port polarity="Input" name="SW0" />
        <port polarity="Output" name="T20" />
        <blockdef name="inv">
            <timestamp>2000-1-1T10:10:10</timestamp>
            <line x2="64" y1="-32" y2="-32" x1="0" />
            <line x2="160" y1="-32" y2="-32" x1="224" />
            <line x2="128" y1="-64" y2="-32" x1="64" />
            <line x2="64" y1="-32" y2="0" x1="128" />
            <line x2="64" y1="0" y2="-64" x1="64" />
            <circle r="16" cx="144" cy="-32" />
        </blockdef>
        <block symbolname="inv" name="XLXI_1">
            <blockpin signalname="T19" name="I" />
            <blockpin signalname="XLXN_2" name="O" />
        </block>
        <block symbolname="inv" name="XLXI_2">
            <blockpin signalname="XLXN_2" name="I" />
            <blockpin signalname="LD0" name="O" />
        </block>
        <block symbolname="inv" name="XLXI_5">
            <blockpin signalname="SW0" name="I" />
            <blockpin signalname="XLXN_7" name="O" />
        </block>
        <block symbolname="inv" name="XLXI_6">
            <blockpin signalname="XLXN_7" name="I" />
            <blockpin signalname="T20" name="O" />
        </block>
    </netlist>
    <sheet sheetnum="1" width="3520" height="2720">
        <branch name="T19">
            <wire x2="848" y1="800" y2="800" x1="832" />
            <wire x2="928" y1="800" y2="800" x1="848" />
        </branch>
        <iomarker fontsize="28" x="832" y="800" name="T19" orien="R180" />
        <instance x="928" y="832" name="XLXI_1" orien="R0" />
        <branch name="XLXN_2">
            <wire x2="1184" y1="800" y2="800" x1="1152" />
        </branch>
        <instance x="1184" y="832" name="XLXI_2" orien="R0" />
        <branch name="LD0">
            <wire x2="1424" y1="800" y2="800" x1="1408" />
            <wire x2="1440" y1="800" y2="800" x1="1424" />
        </branch>
        <iomarker fontsize="28" x="1440" y="800" name="LD0" orien="R0" />
        <branch name="SW0">
            <wire x2="848" y1="976" y2="976" x1="832" />
            <wire x2="912" y1="976" y2="976" x1="848" />
            <wire x2="928" y1="976" y2="976" x1="912" />
        </branch>
        <instance x="928" y="1008" name="XLXI_5" orien="R0" />
        <branch name="XLXN_7">
            <wire x2="1184" y1="976" y2="976" x1="1152" />
        </branch>
        <instance x="1184" y="1008" name="XLXI_6" orien="R0" />
        <branch name="T20">
            <wire x2="1424" y1="976" y2="976" x1="1408" />
            <wire x2="1440" y1="976" y2="976" x1="1424" />
        </branch>
        <iomarker fontsize="28" x="1440" y="976" name="T20" orien="R0" />
        <iomarker fontsize="28" x="832" y="976" name="SW0" orien="R180" />
    </sheet>
</drawing>