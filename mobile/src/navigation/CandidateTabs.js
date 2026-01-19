import React from 'react';
import {View, StyleSheet} from 'react-native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CandidateProfileStack from './CandidateProfileStack';
import CandidateHome from '../screens/Candidate/CandidateHome';
import NotificationsScreen from "../screens/Candidate/Notifications/NotificationsScreen";
import SavedJobsScreen from "../screens/Candidate/SavedJobsScreen";

const NetworkScreen = () => (
    <View style={styles.placeholder}>
        <MaterialCommunityIcons name="account-group" size={50} color="#95969D"/>
    </View>
);

const AddJobScreen = () => (
    <View style={styles.placeholder}>
        <MaterialCommunityIcons name="plus" size={50} color="#95969D"/>
    </View>
);

const MessagesScreen = () => (
    <View style={styles.placeholder}>
        <MaterialCommunityIcons name="message-text" size={50} color="#95969D"/>
    </View>
);

const SavedScreen = () => (
    <View style={styles.placeholder}>
        <MaterialCommunityIcons name="bookmark" size={50} color="#95969D"/>
    </View>
);

const Tab = createBottomTabNavigator();

export default function CandidateTabs() {
    return (
        <Tab.Navigator
            screenOptions={{
                headerShown: false,
                tabBarActiveTintColor: '#0D0140',
                tabBarInactiveTintColor: '#95969D',
                tabBarShowLabel: false,
                tabBarStyle: {
                    backgroundColor: '#fff',
                    borderTopWidth: 0,
                    elevation: 10,
                    shadowColor: '#000',
                    shadowOffset: {width: 0, height: -3},
                    shadowOpacity: 0.1,
                    shadowRadius: 8,
                    height: 70,
                    paddingBottom: 25,
                    paddingTop: 10,
                },
            }}
        >
            <Tab.Screen
                name="Home"
                component={CandidateHome}
                options={{
                    tabBarIcon: ({color, size, focused}) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="home" size={28} color={color}/>
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="Notifications"
                component={NotificationsScreen}
                options={{
                    tabBarIcon: ({color, size, focused}) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="bell-outline" size={28} color={color}/>
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="AddJob"
                component={AddJobScreen}
                options={{
                    tabBarIcon: ({focused}) => (
                        <View style={styles.addButton}>
                            <MaterialCommunityIcons name="plus" size={32} color="#fff"/>
                        </View>
                    ),
                }}

            />
            <Tab.Screen
                name="Saved"
                component={SavedJobsScreen}
                options={{
                    tabBarIcon: ({color, size, focused}) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="bookmark-outline" size={28} color={color}/>
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="Profile"
                component={CandidateProfileStack}
                options={{
                    tabBarIcon: ({color}) => (
                        <MaterialCommunityIcons name="account-outline" size={28} color={color}/>
                    ),
                }}
            />


        </Tab.Navigator>
    );
}

const styles = StyleSheet.create({
    placeholder: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#F5F5F5',
    },
    activeTab: {
        // Optional: Add active state styling
    },
    addButton: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#130160',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 35,
        shadowColor: '#130160',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 3,

    },
});