import React, {useState, useRef, useEffect} from "react";
import {
    View,
    StyleSheet,
    TouchableOpacity,
    Switch,
    Modal,
    TouchableWithoutFeedback,
    Animated,
    Dimensions,
    PanResponder,
} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomText from "../../../components/common/CustomText";
import CustomHeader from "../../../components/common/CustomHeader";

const {height: SCREEN_HEIGHT} = Dimensions.get("window");

const SettingItemCard = ({
                             icon,
                             label,
                             rightType, // "switch" | "chevron"
                             switchValue,
                             onSwitchChange,
                             onPress,
                         }) => {
    return (
        <TouchableOpacity
            activeOpacity={rightType === "chevron" ? 0.85 : 1}
            onPress={rightType === "chevron" ? onPress : undefined}
            style={styles.itemCard}
        >
            <View style={styles.left}>
                <MaterialCommunityIcons name={icon} size={22} color="#201A46"/>
                <CustomText style={styles.itemText}>{label}</CustomText>
            </View>

            {rightType === "switch" ? (
                <Switch
                    value={!!switchValue}
                    onValueChange={onSwitchChange}
                    trackColor={{false: "#E6E6EF", true: "#CFEED1"}}
                    thumbColor={switchValue ? "#33C759" : "#2F2B3A"}
                />
            ) : (
                <MaterialCommunityIcons name="chevron-right" size={24} color="#1D1A3A"/>
            )}
        </TouchableOpacity>
    );
};

const SettingsScreen = ({navigation}) => {
    const [noti, setNoti] = useState(true);
    const [darkMode, setDarkMode] = useState(false);
    const [logoutVisible, setLogoutVisible] = useState(false);

    // ===== Bottom sheet animation (Logout) =====
    const translateY = useRef(new Animated.Value(SCREEN_HEIGHT)).current;

    useEffect(() => {
        if (logoutVisible) {
            translateY.setValue(SCREEN_HEIGHT);
            Animated.spring(translateY, {
                toValue: 0,
                useNativeDriver: true,
                damping: 22,
                stiffness: 160,
            }).start();
        }
    }, [logoutVisible]);

    const closeLogoutSheet = () => {
        Animated.timing(translateY, {
            toValue: SCREEN_HEIGHT,
            duration: 220,
            useNativeDriver: true,
        }).start(() => setLogoutVisible(false));
    };

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, g) => g.dy > 8,
            onPanResponderMove: (_, g) => {
                if (g.dy > 0) translateY.setValue(g.dy);
            },
            onPanResponderRelease: (_, g) => {
                if (g.dy > 120 || g.vy > 0.8) closeLogoutSheet();
                else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        damping: 22,
                        stiffness: 160,
                    }).start();
                }
            },
        })
    ).current;

    const onSave = () => {
        // TODO: API save settings
    };

    const onConfirmLogout = () => {
        closeLogoutSheet();
        // TODO: logout logic
    };

    return (
        <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
            <CustomHeader/>
            <CustomText style={styles.headerTitle}>Settings</CustomText>

            {/* Cards list (mỗi item 1 card) */}
            <View style={styles.list}>
                <SettingItemCard
                    icon="bell-outline"
                    label="Notifications"
                    rightType="switch"
                    switchValue={noti}
                    onSwitchChange={setNoti}
                />

                <SettingItemCard
                    icon="moon-waning-crescent"
                    label="Dark mode"
                    rightType="switch"
                    switchValue={darkMode}
                    onSwitchChange={setDarkMode}
                />

                <SettingItemCard
                    icon="lock-outline"
                    label="Password"
                    rightType="chevron"
                    onPress={() => navigation.navigate("UpdatePassword")}
                />

                <SettingItemCard
                    icon="logout"
                    label="Logout"
                    rightType="chevron"
                    onPress={() => setLogoutVisible(true)}
                />
            </View>

            <View style={styles.bottomArea}>
                <TouchableOpacity activeOpacity={0.9} style={styles.primaryBtn} onPress={onSave}>
                    <CustomText style={styles.primaryText}>SAVE</CustomText>
                </TouchableOpacity>
            </View>

            {/* Logout Bottom Sheet */}
            <Modal visible={logoutVisible} transparent animationType="none" statusBarTranslucent>
                <TouchableWithoutFeedback onPress={closeLogoutSheet}>
                    <View style={styles.sheetOverlay}>
                        <TouchableWithoutFeedback>
                            <Animated.View style={[styles.sheet, {transform: [{translateY}]}]}>
                                <View {...panResponder.panHandlers} style={styles.sheetHandleArea}>
                                    <View style={styles.sheetHandle}/>
                                </View>

                                <CustomText style={styles.sheetTitle}>Log out</CustomText>
                                <CustomText style={styles.sheetSub}>Are you sure you want to leave?</CustomText>

                                <TouchableOpacity
                                    activeOpacity={0.9}
                                    style={[styles.primaryBtn, {width: "100%", marginTop: 18}]}
                                    onPress={onConfirmLogout}
                                >
                                    <CustomText style={styles.primaryText}>YES</CustomText>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    activeOpacity={0.9}
                                    style={styles.secondaryBtn}
                                    onPress={closeLogoutSheet}
                                >
                                    <CustomText style={styles.secondaryText}>CANCEL</CustomText>
                                </TouchableOpacity>
                            </Animated.View>
                        </TouchableWithoutFeedback>
                    </View>
                </TouchableWithoutFeedback>
            </Modal>
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
    backBtn: {
        position: "absolute",
        left: 18,
        top: 14,
        padding: 6
    },
    headerTitle: {
        fontSize: 22,
        fontWeight: "700",
        color: "#150A33",
        marginLeft: 20
    },

    list: {
        paddingHorizontal: 18,
        paddingTop: 24,
        gap: 16
    },
    itemCard: {
        height: 64,
        backgroundColor: "#FFFFFF",
        borderRadius: 16,
        paddingHorizontal: 16,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        shadowColor: "#000",
        shadowOpacity: 0.06,
        shadowRadius: 12,
        shadowOffset: {width: 0, height: 6},
        elevation: 2,
    },
    left: {
        flexDirection: "row",
        alignItems: "center",
        gap: 14
    },
    itemText: {
        fontSize: 15,
        fontWeight: "500",
        color: "#201A46"
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

    sheetOverlay: {
        flex: 1,
        backgroundColor: "rgba(0,0,0,0.35)",
        justifyContent: "flex-end"
    },
    sheet: {
        backgroundColor: "#FFFFFF",
        borderTopLeftRadius: 22,
        borderTopRightRadius: 22,
        paddingHorizontal: 18,
        paddingBottom: 44,
        paddingTop: 10,
    },
    sheetHandleArea: {
        alignItems: "center",
        paddingVertical: 8
    },
    sheetHandle: {
        width: 48,
        height: 5,
        borderRadius: 3,
        backgroundColor: "#E1E0EA"
    },
    sheetTitle: {
        marginTop: 10,
        fontSize: 20,
        fontWeight: "800",
        color: "#201A46",
        textAlign: "center"
    },
    sheetSub: {
        marginTop: 8,
        fontSize: 13,
        fontWeight: "600",
        color: "#9A97AA",
        textAlign: "center"
    },

    secondaryBtn: {
        marginTop: 14,
        width: "100%",
        height: 54,
        borderRadius: 12,
        backgroundColor: "#D6CDFE",
        alignItems: "center",
        justifyContent: "center",
    },
    secondaryText: {
        color: "#FFFFFF",
        fontWeight: "800"
        , letterSpacing: 1
    },
});

export default SettingsScreen;
