#!/usr/bin/python

import array
import os
import usb
import sys


# Accessory ID
HID_ID = 123

# HID report descriptor (stolen from a Logitech K200, consumer descriptor only)
HID_REPORT_DESCRIPTOR = array.array('B', [
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

# Keys
KEY_NONE = 0x00
KEY_NEXT = 0x01
KEY_PREV = 0x02
KEY_STOP = 0x04
KEY_EJECT = 0x08
KEY_PLAY_PAUSE = 0x10
KEY_MUTE = 0x20
KEY_VOL_INC = 0x40
KEY_VOL_DEC = 0x80


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


def send_hid_event(dev, keys):
    print "ACCESSORY_SEND_HID_EVENT ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=57,
        wValue=HID_ID,
        wIndex=0,
        data_or_wLength=array.array('B', [0x03, keys, 0x00, 0x00]))


def handle_accessory(idVendor, idProduct):
    action = {
        "play": KEY_PLAY_PAUSE,
        "next": KEY_NEXT,
        "prev": KEY_PREV,
        "mute": KEY_MUTE,
        "vol+": KEY_VOL_INC,
        "vol-": KEY_VOL_DEC,
        "eject": KEY_EJECT,
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
        wValue=HID_ID,
        wIndex=HID_REPORT_DESCRIPTOR.buffer_info()[1])
    print "ACCESSORY_SET_HID_REPORT_DESC ", dev.ctrl_transfer(
        bmRequestType=0x40,
        bRequest=56,
        wValue=HID_ID,
        wIndex=0,
        data_or_wLength=HID_REPORT_DESCRIPTOR)

    # process actions
    while True:
        try:
            send_hid_event(dev=dev, keys=action[raw_input("> ")])
            send_hid_event(dev=dev, keys=KEY_NONE)
        except KeyError:
            print "unknown action"
        except EOFError:
            print "EOFError"


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
