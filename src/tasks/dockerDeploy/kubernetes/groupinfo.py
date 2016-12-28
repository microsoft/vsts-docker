import hashlib

class GroupInfo(object):
    """
    Holds info about the deployment
    """
    def __init__(self, group_name, group_qualifier, group_version):
        self.name = group_name
        self.qualifier = group_qualifier
        self.version = group_version

    def _get_hash(self, input_string):
        """
        Gets the hashed string
        """
        hash_value = hashlib.sha1(input_string)
        digest = hash_value.hexdigest()
        return digest

    def get_id(self, include_version=True):
        """
        Gets the group id.
        <group_name>.<first 8 chars of SHA-1 hash of group qualifier>.<group_version>
        """
        hash_qualifier = self._get_hash(self.qualifier)[:8]

        if include_version:
            return '{}.{}.{}'.format(self.name, hash_qualifier, self.version)

        return '{}.{}.'.format(self.name, hash_qualifier)
