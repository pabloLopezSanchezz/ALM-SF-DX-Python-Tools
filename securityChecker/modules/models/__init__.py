class ObjectSecurity:
    def __init__(self, sharingModel = None, externalSharingModel= None):
        if not sharingModel:
            self.sharingModel = sharingModel
        else:
            self.sharingModel = sharingModel[0]
        if not externalSharingModel:
            self.externalSharingModel = externalSharingModel
        else:
            self.externalSharingModel = externalSharingModel[0]

class PermissionSecurity:
    def __init__(self, modifyAllData, viewAllData, loginIpRanges, objectPermission):
        self.modifyAllData      = modifyAllData
        self.viewAllData        = viewAllData
        self.loginIpRanges      = loginIpRanges
        self.objectPermission   = objectPermission