#!/usr/bin/env bash
pactl load-module module-native-protocol-tcp port=5050 auth-ip-acl=127.0.0.1
