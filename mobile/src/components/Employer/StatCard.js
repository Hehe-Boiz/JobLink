import { TouchableOpacity, View, Text} from "react-native";
import styles from "../../styles/Employer/EmployerStyles";
import { MaterialCommunityIcons } from '@expo/vector-icons';
const StatCard = ({ icon, color, bg, value, label }) => (
    <TouchableOpacity style={styles.statCardPro} activeOpacity={0.9}>
        <View style={[styles.statIconBox, { backgroundColor: bg }]}>
            <MaterialCommunityIcons name={icon} size={24} color={color} />
        </View>
        <Text style={styles.statNumberPro}>{value}</Text>
        <Text style={styles.statLabelPro}>{label}</Text>
    </TouchableOpacity>
);
export default StatCard;