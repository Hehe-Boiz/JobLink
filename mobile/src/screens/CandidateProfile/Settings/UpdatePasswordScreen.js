import React, {useState} from "react";
import {View, StyleSheet, TouchableOpacity, TextInput} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomText from "../../../components/common/CustomText";
import CustomHeader from "../../../components/common/CustomHeader";

const PasswordInput = ({label, value, onChangeText}) => {
    const [secure, setSecure] = useState(true);

    return (
        <View style={{marginTop: 18}}>
            <CustomText style={styles.label}>{label}</CustomText>
            <View style={styles.inputBox}>
                <TextInput
                    value={value}
                    onChangeText={onChangeText}
                    secureTextEntry={secure}
                    style={styles.input}
                    placeholder=""
                />
                <TouchableOpacity
                    activeOpacity={0.8}
                    onPress={() => setSecure((p) => !p)}
                    style={styles.eyeBtn}
                >
                    <MaterialCommunityIcons
                        name={secure ? "eye-off-outline" : "eye-outline"}
                        size={24}
                        color="#524B6B"
                    />
                </TouchableOpacity>
            </View>
        </View>
    );
};

const UpdatePasswordScreen = ({navigation}) => {
    const [oldPass, setOldPass] = useState("");
    const [newPass, setNewPass] = useState("");
    const [confirm, setConfirm] = useState("");

    const onUpdate = () => {
        // TODO: validate + call API
    };

    return (
        <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
            <CustomHeader/>

            <CustomText style={styles.title}>Update Password</CustomText>


            <View style={styles.body}>
                <PasswordInput label="Old Password" value={oldPass} onChangeText={setOldPass}/>
                <PasswordInput label="New Password" value={newPass} onChangeText={setNewPass}/>
                <PasswordInput label="Confirm Password" value={confirm} onChangeText={setConfirm}/>
            </View>

            <View style={styles.bottomArea}>
                <TouchableOpacity activeOpacity={0.9} style={styles.primaryBtn} onPress={onUpdate}>
                    <CustomText style={styles.primaryText}>UPDATE</CustomText>
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: "#F5F5F7"
    },

    header: {
        height: 56,
        justifyContent: "center",
        paddingHorizontal: 18
    },
    title: {
        fontSize: 20,
        fontWeight: "800",
        color: "#150A33",
        marginLeft: 20
    },

    body: {
        paddingHorizontal: 18,
        paddingTop: 26
    },

    label: {
        fontSize: 16,
        fontWeight: "800",
        color: "#150A33",
        marginBottom: 10
    },

    inputBox: {
        height: 54,
        borderRadius: 12,
        backgroundColor: "#FFFFFF",
        paddingHorizontal: 14,
        flexDirection: "row",
        alignItems: "center",
        borderWidth: 1,
        borderColor: "#ECEAF4",
    },
    input: {
        flex: 1,
        fontSize: 15,
        color: "#3C3754",
        fontWeight: "600",
        padding: 0
    },
    eyeBtn: {
        padding: 6
    },

    bottomArea: {
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 26,
        alignItems: "center"
    },
    primaryBtn: {
        width: 260,
        height: 54,
        borderRadius: 12,
        backgroundColor: "#140B56",
        alignItems: "center",
        justifyContent: "center",
    },
    primaryText: {
        color: "#FFFFFF",
        fontWeight: "800",
        letterSpacing: 1
    },
});

export default UpdatePasswordScreen;
