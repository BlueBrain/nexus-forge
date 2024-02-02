#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.


# Forge operations.

class RunException(Exception):
    pass


class ConfigurationError(Exception):
    pass


class NotSupportedError(Exception):
    pass


# Model operations.


class ValidationError(RunException):
    pass


# Resolver operations.


class ResolvingError(Exception):
    pass


# Store operations.


class RegistrationError(RunException):
    pass


class UploadingError(RunException):
    pass


class RetrievalError(RunException):
    pass


class DownloadingError(RunException):
    pass


class UpdatingError(RunException):
    pass

class SchemaUpdateError(RunException):
    pass

class TaggingError(RunException):
    pass


class DeprecationError(RunException):
    pass


class QueryingError(RunException):
    pass


class FreezingError(RunException):
    pass

# Mapping operations


class MappingLoadError(Exception):
    pass
