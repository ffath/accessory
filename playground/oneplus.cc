#include <algorithm>
#include <iostream>
#include <vector>

#include <string.h>
#include <libusb-1.0/libusb.h>


// returns a vector of open device handles whose product string contains 'Android'
static std::vector<libusb_device_handle *> find_android_devices(libusb_context *ctx) {
	std::vector<libusb_device_handle *> devices;

	// get the devices list
	libusb_device **list = 0;
	ssize_t count = libusb_get_device_list(ctx, &list);

	// search devices for those whose product string contains 'Android'
	for (int i = 0; i < count; i++) {
		int status = LIBUSB_SUCCESS;
		libusb_device *dev = list[i];

		struct libusb_device_descriptor desc;
		if ((status = libusb_get_device_descriptor(dev, &desc) == LIBUSB_SUCCESS)) {
			libusb_device_handle *dev_handle = 0;
			if ((status = libusb_open(dev, &dev_handle)) == LIBUSB_SUCCESS) {
				unsigned char str[256];
				if ((status = libusb_get_string_descriptor_ascii(dev_handle, desc.iProduct, str, sizeof(str) - 1)) >= 0) {
					str[status] = 0; // null-terminate the string just in case
					if (strstr((char *) str, "Android")) {
						// found
						devices.push_back(dev_handle);

						// dump vendor/product id for debug
						std::cout << "found " << std::hex << desc.idVendor << ":" << std::hex << desc.idProduct << " \"" << str << "\"" << std::endl;

						// dont't close or unref
						continue;
					}
				}
				else {
					std::cerr << "libusb_get_string_descriptor_ascii() failed " << libusb_error_name(status) << std::endl;
				}
			}
			else {
				std::cerr << "libusb_open() failed " << libusb_error_name(status) << std::endl;
			}
			libusb_close(dev_handle);
		}
		else {
			std::cerr << "libusb_get_device_descriptor() failed " << libusb_error_name(status) << std::endl;
		}
		libusb_unref_device(dev);
	}

	// cleanup
	libusb_free_device_list(list, false);
	return devices;
}

int main() {
	int status;
	libusb_context *ctx = 0;
	if ((status = libusb_init(&ctx)) != 0) {
		std::cerr << "libusb_init() failed " << libusb_error_name(status) << std::endl;
		return status;
	}

	libusb_set_debug(ctx, 3);

	// get android devices
	std::vector<libusb_device_handle *> devices = find_android_devices(ctx);
	std::cout << "found " << devices.size() << " device" << (devices.size() > 1 ? "s" : "") << std::endl;

	if (devices.size()) {
		libusb_device_handle *dev_handle = devices[0];
		uint16_t data = 0xffff;
		if ((status = libusb_control_transfer(
							dev_handle, 
							LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_ENDPOINT_IN, 
							51, 
							0, 
							0, 
							(unsigned char *) &data, 
							sizeof(data), 
							1000)) >= 0) {
			std::cout << "protocol version = " << std::hex << data << std::endl;

			if (data >= 2) {
				// say hello
				const char *strings[] = {
					"manufacturer",
					"model",
					"description",
					"version",
					"http://www.mystico.org",
					"1"
				};
				for (int i = 2; i < (sizeof(strings) / sizeof(strings[0])); i++) {
					if ((status = libusb_control_transfer(
										dev_handle, 
										LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_ENDPOINT_OUT, 
										52, 
										0, 
										i, 
										(unsigned char *) strings[i], 
										strlen(strings[i]) + 1, 
										1000)) < 0) {
						std::cerr << "libusb_control_transfer(52) index " << i << " failed" << libusb_error_name(status) << std::endl;
					}
				}

				// enable audio support
				if ((status = libusb_control_transfer(
									dev_handle, 
									LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_ENDPOINT_OUT, 
									58, 
									1,	// 2ch 16bit pcm 44100Hz 
									0, 
									nullptr, 
									0, 
									1000)) < 0) {
					std::cerr << "libusb_control_transfer(58) failed" << libusb_error_name(status) << std::endl;
				}

				// start the device in accessory mode
				if ((status = libusb_control_transfer(
									dev_handle, 
									LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_ENDPOINT_OUT, 
									53, 
									0, 
									0, 
									nullptr, 
									0, 
									1000)) < 0) {
					std::cerr << "libusb_control_transfer(53) failed" << libusb_error_name(status) << std::endl;
				}
			}
		}
		else {
			std::cerr << "libusb_control_transfer() failed " << libusb_error_name(status) << std::endl;
		}
	}

	// cleanup
	std::for_each(devices.begin(), devices.end(), [](auto device) { libusb_close(device); });
	libusb_exit(ctx);
}