#!/usr/bin/python

import array
import os
import usb


def main():
    idVendor = int(os.getenv("ID_VENDOR_ID", default="0"), 16)
    idProduct = int(os.getenv("ID_MODEL_ID", default="0"), 16)

    # find device
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        print "Cannot find usb device {0:04x}:{1:04x}".format(
            idVendor, idProduct)
        return

    # GET_PROTOCOL (do you support the protocol, which revision ?)
    data = array.array('B', [0, 0])
    if dev.ctrl_transfer(
            bmRequestType=0xC0, bRequest=51, data_or_wLength=data) != 2:
        print "Device does not support GET_PROTOCOL"
        return

    # must be greater or equal to 2
    version = data[0] + data[1] * 256
    if version < 2:
        print "Protocol version too old ({})".format(version)
        return

    # push the strings
    strings = [
        "manufacturer",
        "model",
        "description",
        "version",
        "http://www.mystico.org",
        "1"]
    for i in range(len(strings)):
        dev.ctrl_transfer(
            bmRequestType=0x40,
            bRequest=52,
            wIndex=i,
            data_or_wLength=strings[i])

    # ask for audio support
    dev.ctrl_transfer(bmRequestType=0x40, bRequest=58, wValue=1)

    # go to accessory mode
    dev.ctrl_transfer(bmRequestType=0x40, bRequest=53)


if __name__ == "__main__":
    main()
