#!/usr/bin/python

import array
import os
import usb
import sys


# HID report descriptor (stolen from an HP keyboard)
'''
hid_report_descriptor = array.array('B', [
    0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x05, 0x07,
    0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01,
    0x75, 0x01, 0x95, 0x08, 0x81, 0x02, 0x95, 0x01,
    0x75, 0x08, 0x81, 0x01, 0x95, 0x03, 0x75, 0x01,
    0x05, 0x08, 0x19, 0x01, 0x29, 0x03, 0x91, 0x02,
    0x95, 0x05, 0x75, 0x01, 0x91, 0x01, 0x95, 0x06,
    0x75, 0x08, 0x15, 0x00, 0x26, 0xff, 0x00, 0x05,
    0x07, 0x19, 0x00, 0x2a, 0xff, 0x00, 0x81, 0x00,
    0xc0
])
'''

# other from logitech
"""
keyboard
0000  05 01 09 06 a1 01 05 07  19 e0 29 e7 15 00 25 01   ........ ..)...%.
0010  75 01 95 08 81 02 95 01  75 08 81 01 95 05 75 01   u....... u.....u.
0020  05 08 19 01 29 05 91 02  95 01 75 03 91 01 95 06   ....)... ..u.....
0030  75 08 15 00 26 ff 00 05  07 19 00 2a ff 00 81 00   u...&... ...*....
0040  c0

media keys
 05 0C 09 01 A1 01 85 01 09 E0 15 E8 25 18 75 07
 95 01 81 06 15 00 25 01 75 01 09 E2 81 06 C0 06
 01 00 09 80 A1 01 85 02 25 01 15 00 75 01 0A 81
 00 0A 82 00 0A 83 00 95 03 81 06 95 05 81 01 C0
 06 0C 00 09 01 A1 01 85 03 25 01 15 00 75 01 0A
 B5 00 0A B6 00 0A B7 00 0A B8 00 0A CD 00 0A E2
 00 0A E9 00 0A EA 00 95 08 81 02 0A 83 01 0A 8A
 01 0A 92 01 0A 94 01 0A 21 02 0A 23 02 0A 24 02
 0A 25 02 95 08 81 02 0A 26 02 0A 27 02 0A 2A 02
 0A B3 00 0A B4 00 95 05 81 02 95 03 81 01 C0
"""

hid_id = 123

# HID report descriptor (stolen from a Logitech K200, consumer descriptor only)
hid_report_descriptor = array.array('B', [
    0x05, 0x0C, 0x09, 0x01, 0xA1, 0x01, 0x85, 0x01,
    0x09, 0xE0, 0x15, 0xE8, 0x25, 0x18, 0x75, 0x07,
    0x95, 0x01, 0x81, 0x06, 0x15, 0x00, 0x25, 0x01,
    0x75, 0x01, 0x09, 0xE2, 0x81, 0x06, 0xC0, 0x06,
    0x01, 0x00, 0x09, 0x80, 0xA1, 0x01, 0x85, 0x02,
    0x25, 0x01, 0x15, 0x00, 0x75, 0x01, 0x0A, 0x81,
    0x00, 0x0A, 0x82, 0x00, 0x0A, 0x83, 0x00, 0x95,
    0x03, 0x81, 0x06, 0x95, 0x05, 0x81, 0x01, 0xC0,
    0x06, 0x0C, 0x00, 0x09, 0x01, 0xA1, 0x01, 0x85,
    0x03, 0x25, 0x01, 0x15, 0x00, 0x75, 0x01, 0x0A,
    0xB5, 0x00, 0x0A, 0xB6, 0x00, 0x0A, 0xB7, 0x00,
    0x0A, 0xB8, 0x00, 0x0A, 0xCD, 0x00, 0x0A, 0xE2,
    0x00, 0x0A, 0xE9, 0x00, 0x0A, 0xEA, 0x00, 0x95,
    0x08, 0x81, 0x02, 0x0A, 0x83, 0x01, 0x0A, 0x8A,
    0x01, 0x0A, 0x92, 0x01, 0x0A, 0x94, 0x01, 0x0A,
    0x21, 0x02, 0x0A, 0x23, 0x02, 0x0A, 0x24, 0x02,
    0x0A, 0x25, 0x02, 0x95, 0x08, 0x81, 0x02, 0x0A,
    0x26, 0x02, 0x0A, 0x27, 0x02, 0x0A, 0x2A, 0x02,
    0x0A, 0xB3, 0x00, 0x0A, 0xB4, 0x00, 0x95, 0x05,
    0x81, 0x02, 0x95, 0x03, 0x81, 0x01, 0xC0
])


def set_accessory_mode(idVendor, idProduct, silent=True):
    # find device
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        print "Cannot find usb device {0:04x}:{1:04x}".format(
            idVendor, idProduct)
        return False

    # GET_PROTOCOL (do you support the protocol, which revision ?)
    data = array.array('B', [0, 0])
    if dev.ctrl_transfer(
            bmRequestType=0xC0, bRequest=51, data_or_wLength=data) != 2:
        print "Device does not support GET_PROTOCOL"
        return False

    # must be greater or equal to 2
    version = data[0] + data[1] * 256
    if version < 2:
        print "Protocol version too old ({})".format(version)
        return False

    # push the strings
    strings = [
        "manufacturer",
        "model",
        "description",
        "version",
        "http://www.mystico.org",
        "1"]

    if silent:
        start_index = 2
    else:
        start_index = 0
    for i in range(start_index, len(strings)):
        dev.ctrl_transfer(
            bmRequestType=0x40,
            bRequest=52,
            wIndex=i,
            data_or_wLength=strings[i])

    # ask for audio support
    dev.ctrl_transfer(bmRequestType=0x40, bRequest=58, wValue=1)

    # go to accessory mode
    dev.ctrl_transfer(bmRequestType=0x40, bRequest=53)

    return True


def play(dev):
    print "PLAY"
    print "ACCESSORY_SEND_HID_EVENT ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=57,
        wValue=hid_id,
        wIndex=0,
        data_or_wLength=array.array('B', [0x03, 0x10, 0x00, 0x00]))
    print "ACCESSORY_SEND_HID_EVENT ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=57,
        wValue=hid_id,
        wIndex=0,
        data_or_wLength=array.array('B', [0x03, 0x00, 0x00, 0x00]))


def next(dev):
    print "NEXT"
    print "ACCESSORY_SEND_HID_EVENT ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=57,
        wValue=hid_id,
        wIndex=0,
        data_or_wLength=array.array('B', [0x03, 0x01, 0x00, 0x00]))
    print "ACCESSORY_SEND_HID_EVENT ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=57,
        wValue=hid_id,
        wIndex=0,
        data_or_wLength=array.array('B', [0x03, 0x00, 0x00, 0x00]))


def handle_accessory(idVendor, idProduct):
    action = {
        "play": play,
        "next": next,
        "quit": quit,
    }

    # find device
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        print "Cannot find usb device {0:04x}:{1:04x}".format(
            idVendor, idProduct)
        return False

    # try and open the hid interface
    print "ACCESSORY_REGISTER_HID ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=54,
        wValue=hid_id,
        wIndex=hid_report_descriptor.buffer_info()[1])
    print "ACCESSORY_SET_HID_REPORT_DESC ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=56,
        wValue=hid_id,
        wIndex=0,
        data_or_wLength=hid_report_descriptor)

    # process actions
    while True:
        try:
            action[raw_input("> ")](dev)
        except KeyError:
            print "unknown action"
        except EOFError:
            print "empty action"


if __name__ == "__main__":
    # get usb ids
    idVendor = int(os.getenv("ID_VENDOR_ID", default="0"), 16)
    idProduct = int(os.getenv("ID_MODEL_ID", default="0"), 16)

    if idVendor == 0x18D1 and idProduct >= 0x2D02 and idProduct <= 0x2D0F:
        # this is an accessory
        if sys.argv.count("--nodaemon") != 0 or os.fork() == 0:
            # find sound card
            # start cvlc or else
            # wait for inputs to forward to the device
            handle_accessory(idVendor, idProduct)
    else:
        set_accessory_mode(idVendor, idProduct)
