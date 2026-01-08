import {StyleSheet} from "react-native";

export default StyleSheet.create({
    tabContainer: {
        flexDirection: 'row',
        backgroundColor: '#FFFFFF',
        borderRadius: 14,
        padding: 5,
        marginHorizontal: 20,
        marginVertical: 20,
        justifyContent: 'space-between',
        height: 50,
        elevation: 1,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowOffset: {width: 0, height: 2}
    },
    tabButton: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 10,
    },
    activeTabButton: {
        backgroundColor: '#FF9228',
    },
    tabText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#95969D',
    },
    activeTabText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
    }
});