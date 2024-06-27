import { format } from "date-fns";
import { UnicornUser, CognitoAttributes, CognitoUser } from "./types";

export function getDateTime(date: string): string {
  return format(new Date(date), "MMMM d, yyyy - H:mm");
}

// Transform cognito format to Unicorn format
export function convertCognitoToUnicorn(cognitoUser: CognitoUser): UnicornUser {
  
  const unicornUser: UnicornUser = {
    username: cognitoUser.username,
    attributes: {},
  };

  cognitoUser.attributes.map((attr: CognitoAttributes) => {
    unicornUser.attributes[attr.Name] = attr.Value;
  });

  return unicornUser;
}

// Transform cognito format to Unicorn format
export function convertUnicornToCognito(unicornUser: UnicornUser): CognitoUser {
  const cognitoAttributes : CognitoAttributes[] = []
  
  const cognitoUser: CognitoUser = {
    username: unicornUser.username,
    attributes: cognitoAttributes,
  };

  Object.keys(unicornUser.attributes).forEach(key => {
    cognitoAttributes.push({
      Name : key,
      Value : unicornUser.attributes[key]
    })
  });

  return cognitoUser;
}

export const departmentList : string[] = [
  "engineering",
  "research",
  "hr"
]

export const accessLevelList : string[] = [
  "support",
  "confidential",
  "public",
]