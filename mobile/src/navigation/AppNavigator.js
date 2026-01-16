import React, { useContext, useEffect } from 'react';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Provider } from 'react-native-paper';
import Login from '../screens/Auth/Login';
import CandidateRegister from '../screens/Auth/CandidateRegister';
import EmployerRegister from '../screens/Auth/EmployerRegister';
import EmployerTabs from './EmployerTabs';
import CandidateTabs from './CandidateTabs';
import CandidateDetail from '../screens/Employer/CandidateDetail';
import PostJob from '../screens/Employer/PostJob';
import EmployerEditProfile from '../screens/Employer/EmployerEditProfile';
import JobDetail from '../screens/Job/JobDetail';
import ApplyJob from "../screens/Job/ApplyJob";
import CandidateSearchResults from "../screens/Candidate/CandidateSearchResults";
import CandidateSearchJob from "../screens/Candidate/CandidateSearchJob";
import CandidateFilterCategory from "../screens/Candidate/CandidateFilterCategory";
import CandidateSearchAdvance from "../screens/Candidate/CandidateSearchAdvance";
import CompanyDetail from '../screens/Candidate/CompanyDetail';
import CandidateProfile from "../screens/CandidateProfile/CandidateProfile";
import EditProfile from "../screens/CandidateProfile/EditProfile";
import EditAboutMe from "../screens/CandidateProfile/EditAboutMe";
import AddWorkExperience from "../screens/CandidateProfile/AddWorkExperience";
import AddEducation from "../screens/CandidateProfile/AddEducation";
import SkillList from "../screens/CandidateProfile/SkillList";
import LanguageList from "../screens/CandidateProfile/LanguageList";
import AppreciationForm from "../screens/CandidateProfile/AppreciationForm";
import AddResume from "../screens/CandidateProfile/AddResume";
import SettingsScreen from "../screens/CandidateProfile/Settings/SettingsScreen";
import UpdatePasswordScreen from "../screens/CandidateProfile/Settings/UpdatePasswordScreen";
import NotificationsScreen from "../screens/Candidate/Notifications/NotificationsScreen";
import NotificationDetailScreen from "../screens/Candidate/Notifications/NotificationDetailScreen";
import AddSkill from "../screens/CandidateProfile/AddSkill";
import AddLanguage from "../screens/CandidateProfile/AddLanguage";
import BuyService from '../screens/Service/BuyService';
import JobApplicants from '../screens/Employer/JobApplicants';
import PaymentResult from '../screens/Service/PaymentResult';
import { MyUserContext } from '../utils/contexts/MyContext';


const Stack = createStackNavigator();


export default function AppNavigator() {
    return (
        <Provider>
            <NavigationContainer>
                <Stack.Navigator
                    initialRouteName="Login"
                    screenOptions={{ headerShown: false }}
                >
                    <Stack.Screen name="Login" component={Login}/>
                    <Stack.Screen name="CandidateRegister" component={CandidateRegister}/>
                    <Stack.Screen name="EmployerRegister" component={EmployerRegister}/>
                    <Stack.Screen name="EmployerMain" component={EmployerTabs}/>
                    <Stack.Screen name="CandidateMain" component={CandidateTabs}/>
                    <Stack.Screen name="JobDetail" component={JobDetail}/>
                    <Stack.Screen name="ApplyJob" component={ApplyJob}/>
                    <Stack.Screen name="JobApplicants" component={JobApplicants}/>
                    <Stack.Screen name="CandidateDetail" component={CandidateDetail}/>
                    <Stack.Screen name="PostJob" component={PostJob}/>
                    <Stack.Screen name="EmployerEditProfile" component={EmployerEditProfile}/>
                    <Stack.Screen name="CandidateSearchResults" component={CandidateSearchResults}/>
                    <Stack.Screen name="CandidateSearchJob" component={CandidateSearchJob}/>
                    <Stack.Screen name="CandidateFilterCategory" component={CandidateFilterCategory}/>
                    <Stack.Screen name="CandidateSearchAdvance" component={CandidateSearchAdvance}/>
                    <Stack.Screen
                        name="JobApplicants"
                        component={JobApplicants}
                        options={{ headerShown: false }}
                    />
                    <Stack.Screen
                        name="PaymentResult"
                        component={PaymentResult}
                        options={{ headerShown: false }}
                    />
                    <Stack.Screen name="BuyService" component={BuyService} />
                    <Stack.Screen name="CompanyDetail" component={CompanyDetail}/>
                    <Stack.Screen name="CandidateProfile" component={CandidateProfile}/>
                    <Stack.Screen name="EditProfile" component={EditProfile}/>
                    <Stack.Screen name="EditAboutMe" component={EditAboutMe}/>
                    <Stack.Screen name="AddWorkExperience" component={AddWorkExperience}/>
                    <Stack.Screen name="AddEducation" component={AddEducation}/>
                    <Stack.Screen name="SkillList" component={SkillList}/>
                    <Stack.Screen name="LanguageList" component={LanguageList}/>
                    <Stack.Screen name="AppreciationForm" component={AppreciationForm}/>
                    <Stack.Screen name="AddResume" component={AddResume}/>
                    <Stack.Screen name="SettingsScreen" component={SettingsScreen}/>
                    <Stack.Screen name="UpdatePasswordScreen" component={UpdatePasswordScreen}/>
                    <Stack.Screen name="Notifications" component={NotificationsScreen}/>
                    <Stack.Screen name="NotificationDetail" component={NotificationDetailScreen}/>
                    <Stack.Screen name="AddSkill" component={AddSkill}/>
                    <Stack.Screen name="AddLanguage" component={AddLanguage}/>

                </Stack.Navigator>
            </NavigationContainer>
        </Provider>
    );
}