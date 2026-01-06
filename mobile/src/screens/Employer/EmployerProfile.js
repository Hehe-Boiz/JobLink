import { use, useContext } from "react";
import { Button } from "react-native-paper";
import { MyUserContext } from "../../utils/contexts/MyContext";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Image, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const EmployerProfile = ({ navigation }) => {
    const [user, dispatch] = useContext(MyUserContext);

    const logout = async () => {
        AsyncStorage.removeItem("token");
        dispatch({
            "type": "logout"
        });
        navigation.reset({
            index: 0,
            routes: [{ name: 'Login' }],
        });
    }
    console.log(user);
    return (
        <SafeAreaView>
            <View>
                <Text>WELCOME {user?.username}!</Text>
                <Button mode="contained-tonal" icon="account" onPress={logout}>Đăng xuất</Button>
            </View>
        </SafeAreaView>
    );
}

export default EmployerProfile;