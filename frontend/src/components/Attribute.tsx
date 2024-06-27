import { useState, useEffect } from "react";
import { API } from "aws-amplify";
import { UnicornUser, CognitoUser } from "../common/types";
import { convertCognitoToUnicorn, convertUnicornToCognito, departmentList, accessLevelList } from "../common/utilities"


const Attributes: React.FC = () => {
  const [users, setUsers] = useState<UnicornUser[]>([]);
  const [editUnicornUser, setEditUnicornUser] = useState<UnicornUser | null >();
  const [attributeStatus, setAttributeStatus] = useState<string>("idle");

  const fetchAttributes = async () => {
    setAttributeStatus("loading");

    const response = await API.get("RestApi", "/access", {});
    
    // Parse users
    const unicornUsers = response.users.map((user: CognitoUser) => {
      return convertCognitoToUnicorn(user)
    })

    console.log('unicornusers')
    console.log(unicornUsers)

    // Parse users
    const back = unicornUsers.map((user: UnicornUser) => {
      return convertUnicornToCognito(user)
    })
    

    console.log('back')
    console.log(back)



    setUsers(unicornUsers)
    setAttributeStatus("idle");
  };

  const handleEditClick = async (i: number) => {
    setAttributeStatus("idle")
    setEditUnicornUser(users[i])
    console.log(users[i])
  }

  const handleSaveClick = async () => {
    // TODO : Submit attributes update.
    console.log("SAVED")
    setAttributeStatus("Successful")
    setEditUnicornUser(null)
  }

  const onDepartmentSelect = (department:string) => {
    const newUser = editUnicornUser;
    newUser!.attributes['custom:department'] = department
    setEditUnicornUser(newUser)
    console.log(editUnicornUser)
  }

  const onAccessLevelSelect = (access_level:string) => {
    editUnicornUser!.attributes['custom:access_level'] = access_level
    console.log(editUnicornUser)
  }

  useEffect(() => {
    fetchAttributes()
  }, []);

  return (
    <div className="justify-between pt-6 pb-4">
      {
        attributeStatus == "Successful" && (
          <div className="bg-teal-100 border-t-4 border-teal-500 rounded-b text-teal-900 px-4 py-3 shadow-md" role="alert">
            <div className="flex">
              <div className="py-1"><svg className="fill-current h-6 w-6 text-teal-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM9 11V9h2v6H9v-4zm0-6h2v2H9V5z"/></svg></div>
              <div>
                <p className="font-bold">Attributes updated successfully.</p>
              </div>
            </div>
          </div>
        )
      }
      <div className="w-full border-b-2 border-gray-300 pb-4">
        <h2 className="text-2xl font-bold">Manage permission</h2>
      </div>

      <div className="relative overflow-x-auto shadow-md sm:rounded-lg">
          <table className="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                  <tr>
                      <th scope="col" className="px-6 py-3">
                          User Name
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Email
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Department
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Access Level
                      </th>
                      <th scope="col" className="px-6 py-3">
                          <span className="sr-only">Edit</span>
                      </th>
                  </tr>
              </thead>
              <tbody>
                {
                  users.map((unicornUser, i) => (
                    <tr className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                        key={`${'row_'+i}`}
                    >
                        <th scope="row" className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                          {unicornUser.username}
                        </th>
                        <td className="px-6 py-4">
                          {unicornUser.attributes.email}
                        </td>

                        <td className="px-6 py-4">
                          <select id={`${i + 'department_select'}`} className="block py-2.5 px-0 w-full text-sm text-gray-500 bg-transparent border-0 border-b-2 border-gray-200 appearance-none dark:text-gray-400 dark:border-gray-700 focus:outline-none focus:ring-0 focus:border-gray-200 peer"
                            disabled={!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)}
                            defaultValue={unicornUser.attributes["custom:department"]}
                          >
                          {departmentList.map((department) => (
                            <option key={`${i+'_'+department}`} value={department}
                                    onSelect={() => onDepartmentSelect(department)}>
                              {department}
                            </option>
                          ))}
                          </select>
                        </td>

                        <td className="px-6 py-4">
                          <select id={`${i + 'access_control_select'}`} className="block py-2.5 px-0 w-full text-sm text-gray-500 bg-transparent border-0 border-b-2 border-gray-200 appearance-none dark:text-gray-400 dark:border-gray-700 focus:outline-none focus:ring-0 focus:border-gray-200 peer"
                            disabled={!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)}
                            defaultValue={unicornUser.attributes["custom:access_level"]}
                          >
                          {accessLevelList.map((accessLevel) => (
                            <option key={`${i+'_'+accessLevel}`} value={accessLevel}
                                    onSelect={() => onAccessLevelSelect(accessLevel)}
                            >
                              {accessLevel}
                            </option>
                          ))}
                          </select>
                        </td>


                        <td className="px-6 py-4 text-right">
                            {(!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)) && (
                              <button type="button" 
                                className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                                onClick={() => handleEditClick(i)}
                              >
                              Edit
                            </button> )
                            }

                            {editUnicornUser && editUnicornUser.attributes.sub === unicornUser.attributes.sub && (
                              <button type="button" 
                                className="text-white bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 hover:bg-gradient-to-br focus:ring-4 focus:outline-none focus:ring-blue-300 dark:focus:ring-blue-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center me-2 mb-2"
                                onClick={() => handleSaveClick()}
                              >
                              Save
                            </button> )
                            }

                        </td>
                    </tr>
                  ))
                }
              </tbody>
          </table>
      </div>

    </div>
  );
};

export default Attributes;