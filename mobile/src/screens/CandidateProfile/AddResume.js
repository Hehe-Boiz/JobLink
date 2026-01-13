import React, {useState} from "react";
import {View, TouchableOpacity, Image, Alert, StyleSheet} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomHeader from "../../components/common/CustomHeader";
import CustomText from "../../components/common/CustomText";
import styles from "../../styles/Job/ApplyJobStyles";
import myStyles from "../../styles/MyStyles";

import * as DocumentPicker from "expo-document-picker";

const AddResume = ({navigation}) => {
    const [resume, setResume] = useState(null);

    const pickPdf = async () => {
        const res = await DocumentPicker.getDocumentAsync({
            type: ["application/pdf"],
            multiple: false,
            copyToCacheDirectory: true,
        });

        if (res.canceled) return;

        const file = res.assets?.[0];
        if (!file) return;

        // check 5MB
        if (typeof file.size === "number" && file.size > 5 * 1024 * 1024) {
            Alert.alert("File too large", "Max size is 5MB.");
            return;
        }

        setResume({
            name: file.name,
            size: file.size,
            uri: file.uri,
            mimeType: file.mimeType,
        });
    };

    const removeFile = () => setResume(null);

    const formatKb = (bytes) =>
        typeof bytes === "number" ? `${Math.round(bytes / 1024)} Kb` : "";

    return (
        <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
            <CustomHeader navigation={navigation} title=""/>

            <View style={{paddingHorizontal: 20, paddingTop: 10}}>
                <CustomText style={localStyles.title}>
                    Add Resume
                </CustomText>

                {!resume ? (
                    <TouchableOpacity activeOpacity={0.9} style={styles.uploadBox} onPress={pickPdf}>
                        <MaterialCommunityIcons name="upload" size={22} color="#150B3D"/>
                        <CustomText style={styles.uploadText}>Upload CV/Resume</CustomText>
                    </TouchableOpacity>
                ) : (
                    <View style={styles.fileSuccessContainer}>
                        <View style={styles.filePreviewContainer}>
                            <View style={styles.fileIconBox}>
                                <MaterialCommunityIcons name="file-pdf-box" size={40} color="#FF4D4D"/>
                            </View>

                            <View style={styles.fileInfo}>
                                <CustomText style={styles.fileName} numberOfLines={1}>
                                    {resume.name}
                                </CustomText>
                                <CustomText style={styles.fileSize}>
                                    {(resume.size / 1024).toFixed(0)} Kb • {new Date().toLocaleDateString()}
                                </CustomText>
                            </View>

                            <TouchableOpacity style={styles.removeBtn} onPress={pickPdf}>
                                <MaterialCommunityIcons name="pencil-outline" size={20} color="#130160"/>
                            </TouchableOpacity>
                        </View>

                        <TouchableOpacity
                            style={{flexDirection: 'row', alignItems: 'center', marginTop: 10}}
                            onPress={removeFile}
                        >
                            <MaterialCommunityIcons name="trash-can-outline" size={24} color="#FF4D4D"/>
                            <CustomText style={[styles.removeText, myStyles.mb1, {fontSize: 14}]}>Remove
                                file</CustomText>
                        </TouchableOpacity>
                    </View>
                )}

                <CustomText
                    style={localStyles.desc}>
                    Upload files in PDF format up to 5 MB. Just upload it once and you can use it in your next
                    application.
                </CustomText>
            </View>

            <View style={localStyles.btnSave}>
                <TouchableOpacity
                    activeOpacity={0.9}
                    style={[styles.applyBtn, !resume && {opacity: 0.5}]}
                    disabled={!resume}
                    onPress={() => navigation.goBack()}
                >
                    <CustomText style={styles.applyBtnText}>SAVE</CustomText>
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
};

export default AddResume;

const localStyles = StyleSheet.create({
    title: {
        fontSize: 22,
        fontWeight: "600",
        color: "#150A33",
        marginBottom: 30,
    },
    btnSave: {
        position: "absolute",
        left: 60,
        right: 60,
        bottom: 25
    },
    desc: {
        marginTop: 18,
        fontSize: 14,
        color: "#AAA6B9",
        fontWeight: "500",
        lineHeight: 18
    }

})
