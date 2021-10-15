#!/usr/bin/env bash

# [API] Get list of users
curl --location --request GET 'http://localhost:9000/api/v1/user/'

# E.g.
# {
#     "success": [
#         {
#             "id": "dd0aed9e-589c-4764-aa55-c9fa65f7e0ab",
#             "username": "kshaa"
#         }
#     ]
# }

# [API] Create new user
curl --location --request POST 'http://localhost:9000/api/v1/user/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "kshaa",
    "password": "qwerty123"
}'

# E.g.
# {
#     "success": {
#         "id": "2928ddee-2e6f-4882-b494-f156d8af37a8",
#         "username": "kshaa2"
#     }
# }

# [API] Get list of hardware
curl --location --request GET 'http://localhost:9000/api/v1/hardware/' \
--header 'Authentication: Basic a3NoYWE6cXdlcnR5MTIz'

# E.g.
# {
#     "success": [
#         {
#             "id": "e61aeddd-1119-49b6-9a8e-6c0405c437f1",
#             "name": "anvyl-01",
#             "batteryPercent": 0.0,
#             "ownerId": "dd0aed9e-589c-4764-aa55-c9fa65f7e0ab"
#         }
#     ]
# }

# [API] Create new hardware
# Note: `Authentication` contains base64 encoded `kshaa:qwerty123` 
curl --location --request POST 'http://localhost:9000/api/v1/hardware/' \
--header 'Authentication: Basic a3NoYWE6cXdlcnR5MTIz' \ 
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "anvyl-01"
}'

# E.g.
# Note `batteryPercent` will be removed
# {
#     "success": {
#         "id": "b7640937-905e-4c2d-acc0-832c2732c17e",
#         "name": "anvyl-02",
#         "batteryPercent": 0.0,
#         "ownerId": "dd0aed9e-589c-4764-aa55-c9fa65f7e0ab"
#     }
# }

# [API] Get a list of software
curl --location --request GET 'http://localhost:9000/api/v1/software/'

# E.g.
# {
#     "success": [
#         {
#             "id": "bc829ad0-4a52-4d10-b599-c4193fa2cf28",
#             "ownerId": "dd0aed9e-589c-4764-aa55-c9fa65f7e0ab",
#             "name": "test"
#         }
#     ]
# }

# [API] Download software
curl --location --request GET 'http://localhost:9000/api/v1/software/218e353b-ba7d-42b7-8912-df552f4bcfb1/download'

# E.g.
# <binary file blob>

# [API] Upload new software
# Note: `Authentication` contains base64 encoded `kshaa:qwerty123` 
curl --location --request POST 'http://localhost:9000/api/v1/software/' \
--header 'Authentication: Basic a3NoYWE6cXdlcnR5MTIz' \
--form 'software=@"/home/kveinbahs/Code/dip-testbed/notes/firmware.hex"' \
--form 'name="hello_firmware_2.hex"'

# E.g.
# {
#     "success": {
#         "id": "07bfa8ca-4ec5-4c26-95e5-f099123cbeb1",
#         "ownerId": "dd0aed9e-589c-4764-aa55-c9fa65f7e0ab",
#         "name": "hello_firmware_2.hex"
#     }
# }

# [API] Initiate agent control connection
websocat "http://localhost:9000/api/v1/hardware/b7640937-905e-4c2d-acc0-832c2732c17e/control"

# E.g.
# {
#     "command": "uploadSoftwareRequest",
#     "payload": { 
#         "softwareId": "16d7ce54-2d10-11ec-a35e-d79560b12f04"
#     }
# }

# [API] Request hardware software upload
# Note: `Authentication` contains base64 encoded `kshaa:qwerty123` 
curl --location --request GET \
'http://localhost:9000/api/v1/hardware/e61aeddd-1119-49b6-9a8e-6c0405c437f1/upload/software/82b0a3ce-3230-4b18-8552-84feea7383f4' \
--header 'Authentication: Basic a3NoYWE6cXdlcnR5MTIz'

# E.g.
# {
#   "success" : {}
# }

# E.g.
# <exception message thrown when hardware is not online>