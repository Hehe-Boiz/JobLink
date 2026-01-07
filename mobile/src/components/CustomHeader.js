import styles from "../styles/Job/JobDetailStyles";
import {TouchableOpacity, View} from "react-native";
import React from "react";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import {useNavigation} from '@react-navigation/native';

const CustomHeader = ({navigation, iconColor = "#1A1D1F", showMenu = true}) => {
    // const navigation = useNavigation();
    return (
        <View style={styles.headerNav}>
            <TouchableOpacity onPress={() => navigation?.canGoBack() ? navigation.goBack() : null}>
                <MaterialCommunityIcons name="arrow-left" size={24} color={iconColor}/>
            </TouchableOpacity>
            {showMenu ? (
                <TouchableOpacity>
                    <MaterialCommunityIcons name="dots-horizontal" size={24} color={iconColor}/>
                </TouchableOpacity>) : (<View style={{width: 24}}/>)}

        </View>
    );
};

export default CustomHeader